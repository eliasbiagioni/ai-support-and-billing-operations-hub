"""WebSocket copilot tests: real-time events + full-history persistence (PRD 14.1).

Uses a scripted tool-calling LLM (no network) and a minted JWT to exercise the
``/api/ai/copilot/ws`` channel end to end, asserting that (a) tool activity and
answers are streamed as events, (b) turns are persisted, and (c) the entire
prior conversation is replayed to the model on the next question.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from app.core.security import create_access_token
from app.integrations.llm_client import ChatResult, ToolCall, get_llm_client
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


class ScriptedLLM:
    """Returns pre-scripted chat turns and records the last messages it saw."""

    def __init__(self, turns: list[ChatResult]) -> None:
        self._turns = list(turns)
        self.chat_calls = 0
        self.last_messages: list[dict[str, Any]] = []

    def chat(self, *, messages, tools=None):  # type: ignore[no-untyped-def]
        self.chat_calls += 1
        self.last_messages = list(messages)
        if self._turns:
            return self._turns.pop(0)
        return ChatResult(content="Done.", tool_calls=[])

    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        return ""

    def embed(self, texts):  # type: ignore[no-untyped-def]
        return [[0.0] for _ in texts]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _token_for(make_user: Callable[..., User]) -> tuple[User, str]:
    user = make_user("agent@acme.io", role=UserRole.admin)
    token = create_access_token(subject=user.id, role=user.role.value)
    return user, token


def _create_customer(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/customers",
        json={"company_name": "Acme Co", "email": "ops@acme.example"},
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_article(client: TestClient, token: str) -> None:
    response = client.post(
        "/api/knowledge/articles",
        json={
            "title": "Refund policy",
            "content": "We offer prorated refunds within 14 days of a charge.",
            "tags": ["refund", "billing"],
            "visibility": "public",
        },
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text


def _recv_until_answer(ws) -> tuple[dict[str, Any], list[dict[str, Any]]]:  # type: ignore[no-untyped-def]
    events: list[dict[str, Any]] = []
    while True:
        event = ws.receive_json()
        events.append(event)
        if event["type"] == "answer":
            return event, events


def test_copilot_ws_streams_and_persists_history(
    api_client: TestClient, make_user: Callable[..., User]
) -> None:
    user, token = _token_for(make_user)
    customer_id = _create_customer(api_client, token)
    _create_article(api_client, token)

    fake = ScriptedLLM(
        [
            # Turn 1: search the KB, then answer.
            ChatResult(
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="search_knowledge",
                        arguments={"query": "refund", "limit": 5},
                    )
                ]
            ),
            ChatResult(content="Refunds are prorated within 14 days of a charge."),
            # Turn 2: answer directly (relies on prior context).
            ChatResult(content="Yes, that 14-day window still applies."),
        ]
    )
    app.dependency_overrides[get_llm_client] = lambda: fake

    with api_client.websocket_connect(
        f"/api/ai/copilot/ws?token={token}&customer_id={customer_id}"
    ) as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        conversation_id = ready["conversation_id"]
        assert ready["history"] == []

        ws.send_json({"message": "What is our refund policy?"})
        answer1, events1 = _recv_until_answer(ws)
        assert "refund" in answer1["answer"].lower()
        assert "search_knowledge" in answer1["tools_called"]
        assert len(answer1["citations"]) >= 1
        # The tool call was surfaced as a real-time event.
        assert any(e["type"] == "tool_activity" for e in events1)

        ws.send_json({"message": "And within how many days?"})
        answer2, _ = _recv_until_answer(ws)
        assert "14" in answer2["answer"]

    # The second turn must have replayed the full prior conversation.
    contents = [str(m.get("content", "")) for m in fake.last_messages]
    roles = [m.get("role") for m in fake.last_messages]
    assert any("refund policy" in c.lower() for c in contents)
    assert "assistant" in roles

    # Everything is persisted and retrievable.
    detail = api_client.get(
        f"/api/ai/conversations/{conversation_id}", headers=_headers(token)
    )
    assert detail.status_code == 200, detail.text
    messages = detail.json()["messages"]
    assert [m["role"] for m in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    listing = api_client.get("/api/ai/conversations", headers=_headers(token))
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1


def test_copilot_ws_rejects_missing_token(api_client: TestClient) -> None:
    # The server accepts then closes unauthenticated sockets with code 4401.
    with (
        api_client.websocket_connect("/api/ai/copilot/ws") as ws,
        pytest.raises(WebSocketDisconnect) as excinfo,
    ):
        ws.receive_json()
    assert excinfo.value.code == 4401
