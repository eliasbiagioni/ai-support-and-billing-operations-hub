"""Knowledge base tests: CRUD, chunking, and search (PRD 14.1)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def _create_article(client: TestClient, **overrides: object) -> dict:
    payload = {
        "title": "Refund policy",
        "content": (
            "We offer prorated refunds within 14 days.\n\n"
            "Refunds go back to the original payment method."
        ),
        "tags": ["refund", "billing"],
        "visibility": "public",
    }
    payload.update(overrides)
    response = client.post("/api/knowledge/articles", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_article_generates_chunks(client: TestClient) -> None:
    article = _create_article(client)
    assert article["title"] == "Refund policy"
    assert article["tags"] == ["refund", "billing"]
    assert article["chunk_count"] >= 1


def test_get_and_list_articles(client: TestClient) -> None:
    _create_article(client, title="Cancellation policy", tags=["cancel"])
    listing = client.get("/api/knowledge/articles")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    article_id = listing.json()["items"][0]["id"]
    detail = client.get(f"/api/knowledge/articles/{article_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == article_id


def test_update_article_rechunks(client: TestClient) -> None:
    article = _create_article(client)
    long_content = "\n\n".join(f"Paragraph {i} " + "x" * 300 for i in range(4))
    response = client.patch(
        f"/api/knowledge/articles/{article['id']}",
        json={"content": long_content},
    )
    assert response.status_code == 200
    assert response.json()["chunk_count"] >= 2


def test_search_returns_source_metadata(client: TestClient) -> None:
    _create_article(client)
    response = client.get("/api/knowledge/search", params={"q": "refund"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["title"] == "Refund policy"
    assert "snippet" in results[0]
    assert results[0]["chunk_id"] is not None


def test_get_missing_article_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/knowledge/articles/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
