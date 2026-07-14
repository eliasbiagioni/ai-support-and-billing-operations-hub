"""Copilot tests using a scripted tool-calling LLM (no network) (PRD 14.1)."""

from __future__ import annotations

from app.integrations.llm_client import ChatResult, ToolCall, get_llm_client
from app.main import app
from fastapi.testclient import TestClient


class ScriptedLLM:
    """Returns pre-scripted chat turns so the tool loop is deterministic."""

    def __init__(self, turns: list[ChatResult]) -> None:
        self._turns = list(turns)
        self.chat_calls = 0

    def chat(self, *, messages, tools=None):  # type: ignore[no-untyped-def]
        self.chat_calls += 1
        if self._turns:
            return self._turns.pop(0)
        return ChatResult(content="Done.", tool_calls=[])

    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        return ""

    def embed(self, texts):  # type: ignore[no-untyped-def]
        return [[0.0] for _ in texts]


def _use_llm(fake: ScriptedLLM) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake


def _create_article(client: TestClient) -> str:
    response = client.post(
        "/api/knowledge/articles",
        json={
            "title": "Refund policy",
            "content": "We offer prorated refunds within 14 days of a charge.",
            "tags": ["refund", "billing"],
            "visibility": "public",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_copilot_uses_tools_and_cites(client: TestClient, customer_id: str) -> None:
    _create_article(client)
    _use_llm(
        ScriptedLLM(
            [
                ChatResult(
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            name="search_knowledge",
                            arguments={"query": "refund", "limit": 5},
                        )
                    ]
                ),
                ChatResult(
                    content="Refunds are prorated within 14 days of a charge."
                ),
            ]
        )
    )

    response = client.post(
        "/api/ai/copilot",
        json={"message": "What is our refund policy?", "customer_id": customer_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "refund" in body["answer"].lower()
    assert "search_knowledge" in body["tools_called"]
    assert len(body["citations"]) >= 1
    assert body["citations"][0]["title"] == "Refund policy"

    logs = client.get("/api/ai/audit-logs", params={"action_type": "copilot"})
    assert logs.status_code == 200
    items = logs.json()["items"]
    assert items and items[0]["action_type"] == "copilot"
    assert "search_knowledge" in items[0]["tools_called"]


def test_copilot_proposes_risky_action(client: TestClient, customer_id: str) -> None:
    _use_llm(
        ScriptedLLM(
            [
                ChatResult(
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            name="propose_checkout_session",
                            arguments={
                                "customer_id": customer_id,
                                "reason": "Upgrade to Pro plan",
                            },
                        )
                    ]
                ),
                ChatResult(
                    content="I've queued a checkout for your approval."
                ),
            ]
        )
    )

    response = client.post(
        "/api/ai/copilot",
        json={
            "message": "Upgrade this customer to Pro",
            "customer_id": customer_id,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["proposed_actions"], body
    action = body["proposed_actions"][0]
    assert action["type"] == "checkout_session"
    assert action["requires_approval"] is True
    assert "proposed_action" in body["risk_flags"]
