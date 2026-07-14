"""AI Assist tests using a fake LLM client (no network calls) (PRD 14.1)."""

from __future__ import annotations

import json

from app.integrations.llm_client import LLMClient, get_llm_client
from app.main import app
from fastapi.testclient import TestClient


class FakeLLM:
    """Deterministic stand-in for the OpenAI client."""

    def __init__(self, *, json_response: str | None = None, text: str = "A reply.") -> None:
        self._json_response = json_response
        self._text = text
        self.calls = 0

    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        self.calls += 1
        if json_mode:
            return self._json_response if self._json_response is not None else "{}"
        return self._text


def _use_llm(fake: LLMClient) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake


def _create_ticket(client: TestClient, customer_id: str) -> str:
    response = client.post(
        "/api/tickets",
        json={
            "customer_id": customer_id,
            "subject": "Payment failed",
            "description": "My card was declined twice.",
            "category": "billing",
            "priority": "high",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_classify_returns_structured_output(client: TestClient, customer_id: str) -> None:
    ticket_id = _create_ticket(client, customer_id)
    _use_llm(
        FakeLLM(
            json_response=json.dumps(
                {
                    "category": "billing",
                    "urgency": "high",
                    "sentiment": "negative",
                    "billing_lookup_required": True,
                    "suggested_team": "billing",
                    "reasoning_summary": "Customer reports a failed payment.",
                }
            )
        )
    )

    response = client.post(f"/api/ai/tickets/{ticket_id}/classify")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["category"] == "billing"
    assert body["urgency"] == "high"
    assert body["billing_lookup_required"] is True


def test_classify_invalid_json_fails_safely(client: TestClient, customer_id: str) -> None:
    ticket_id = _create_ticket(client, customer_id)
    fake = FakeLLM(json_response="not json at all")
    _use_llm(fake)

    response = client.post(f"/api/ai/tickets/{ticket_id}/classify")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ai_processing_error"
    # It retried once before failing.
    assert fake.calls == 2


def test_classify_normalizes_bad_sentiment(client: TestClient, customer_id: str) -> None:
    ticket_id = _create_ticket(client, customer_id)
    _use_llm(
        FakeLLM(
            json_response=json.dumps(
                {
                    "category": "technical",
                    "urgency": "medium",
                    "sentiment": "furious",
                    "billing_lookup_required": False,
                    "suggested_team": "support",
                    "reasoning_summary": "",
                }
            )
        )
    )
    response = client.post(f"/api/ai/tickets/{ticket_id}/classify")
    assert response.status_code == 200
    assert response.json()["sentiment"] == "neutral"


def test_summarize_and_audit_log(client: TestClient, customer_id: str) -> None:
    ticket_id = _create_ticket(client, customer_id)
    _use_llm(FakeLLM(text="- Customer had a failed payment\n- Card declined twice"))

    response = client.post(f"/api/ai/tickets/{ticket_id}/summarize")
    assert response.status_code == 200
    assert "failed payment" in response.json()["summary"]

    logs = client.get("/api/ai/audit-logs", params={"ticket_id": ticket_id})
    assert logs.status_code == 200
    body = logs.json()
    assert body["total"] == 1
    assert body["items"][0]["action_type"] == "summarize"


def test_suggest_reply_flags_human_review(client: TestClient, customer_id: str) -> None:
    ticket_id = _create_ticket(client, customer_id)
    _use_llm(FakeLLM(text="Hi, sorry to hear that. Please update your card and retry."))

    response = client.post(f"/api/ai/tickets/{ticket_id}/suggest-reply")
    assert response.status_code == 200
    assert "update your card" in response.json()["reply"]

    logs = client.get(
        "/api/ai/audit-logs", params={"ticket_id": ticket_id, "action_type": "suggest_reply"}
    )
    assert logs.json()["items"][0]["risk_flags"] == ["human_review_required"]
