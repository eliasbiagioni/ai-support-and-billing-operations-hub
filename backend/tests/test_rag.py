"""RAG tests: keyword-based fake embeddings + SQLite cosine fallback."""

from __future__ import annotations

from app.integrations.llm_client import (
    ChatResult,
    get_llm_client,
    get_optional_llm_client,
)
from app.main import app
from fastapi.testclient import TestClient

_VOCAB = ["refund", "payment", "security", "onboarding", "invoice", "plan"]


def _vec(text: str) -> list[float]:
    lowered = text.lower()
    vector = [float(lowered.count(word)) for word in _VOCAB]
    if not any(vector):
        vector = [1.0] + [0.0] * (len(_VOCAB) - 1)
    return vector


class FakeEmbedLLM:
    """Deterministic keyword-count embeddings so cosine is meaningful."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_vec(text) for text in texts]

    def complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        return "Here is a drafted reply grounded in our policy."

    def chat(self, *, messages, tools=None):  # type: ignore[no-untyped-def]
        return ChatResult(content="ok")


def _use_fake() -> FakeEmbedLLM:
    fake = FakeEmbedLLM()
    app.dependency_overrides[get_llm_client] = lambda: fake
    app.dependency_overrides[get_optional_llm_client] = lambda: fake
    return fake


def _create_article(client: TestClient, title: str, content: str, tags: list[str]) -> None:
    response = client.post(
        "/api/knowledge/articles",
        json={"title": title, "content": content, "tags": tags, "visibility": "public"},
    )
    assert response.status_code == 201, response.text


def _seed_articles(client: TestClient) -> None:
    _create_article(
        client,
        "Refund policy",
        "We offer prorated refunds within 14 days. A refund goes to the original payment method.",
        ["refund", "billing"],
    )
    _create_article(
        client,
        "Security and data handling",
        "Data is encrypted at rest. Report security incidents to the security team.",
        ["security"],
    )


def test_semantic_suggest_reply_cites_relevant_article(
    client: TestClient, customer_id: str
) -> None:
    _use_fake()
    _seed_articles(client)

    ticket = client.post(
        "/api/tickets",
        json={
            "customer_id": customer_id,
            "subject": "Refund request",
            "description": "I want a refund for my recent payment.",
            "category": "billing",
            "priority": "high",
        },
    )
    assert ticket.status_code == 201, ticket.text
    ticket_id = ticket.json()["id"]

    response = client.post(f"/api/ai/tickets/{ticket_id}/suggest-reply")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"]
    assert "human_review_required" in body["risk_flags"]
    assert body["citations"], "expected RAG citations"
    assert body["citations"][0]["title"] == "Refund policy"


def test_semantic_search_ranks_by_similarity(
    client: TestClient, customer_id: str
) -> None:
    _use_fake()
    _seed_articles(client)

    ticket = client.post(
        "/api/tickets",
        json={
            "customer_id": customer_id,
            "subject": "Security question",
            "description": "How does your security and data encryption work?",
            "category": "technical",
            "priority": "low",
        },
    )
    ticket_id = ticket.json()["id"]

    response = client.post(f"/api/ai/tickets/{ticket_id}/suggest-reply")
    assert response.status_code == 200, response.text
    citations = response.json()["citations"]
    assert citations
    assert citations[0]["title"] == "Security and data handling"
