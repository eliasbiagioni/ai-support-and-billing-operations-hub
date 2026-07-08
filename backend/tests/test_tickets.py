"""Ticket workflow tests: creation, transitions, messages, resolve (PRD 14.1)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_ticket(client: TestClient, customer_id: int, **overrides: object) -> dict:
    payload = {
        "customer_id": customer_id,
        "subject": "Payment failed",
        "description": "My card was declined.",
        "category": "billing",
        "priority": "high",
    }
    payload.update(overrides)
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_ticket(client: TestClient, customer_id: int) -> None:
    ticket = _create_ticket(client, customer_id)
    assert ticket["subject"] == "Payment failed"
    assert ticket["status"] == "new"
    assert ticket["category"] == "billing"
    assert ticket["messages"] == []


def test_create_ticket_unknown_customer(client: TestClient) -> None:
    response = client.post(
        "/api/tickets",
        json={
            "customer_id": 4242,
            "subject": "Test",
            "description": "Body",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_valid_status_transition(client: TestClient, customer_id: int) -> None:
    ticket = _create_ticket(client, customer_id)
    response = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "open"})
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_invalid_status_transition_conflicts(client: TestClient, customer_id: int) -> None:
    ticket = _create_ticket(client, customer_id)
    client.patch(f"/api/tickets/{ticket['id']}", json={"status": "closed"})
    # closed -> resolved is not allowed
    response = client.patch(f"/api/tickets/{ticket['id']}", json={"status": "resolved"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_resolve_ticket(client: TestClient, customer_id: int) -> None:
    ticket = _create_ticket(client, customer_id)
    response = client.post(f"/api/tickets/{ticket['id']}/resolve")
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_add_message_to_ticket(client: TestClient, customer_id: int) -> None:
    ticket = _create_ticket(client, customer_id)
    response = client.post(
        f"/api/tickets/{ticket['id']}/messages",
        json={"body": "Looking into this now.", "author_type": "agent"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["body"] == "Looking into this now."
    assert body["author_type"] == "agent"

    detail = client.get(f"/api/tickets/{ticket['id']}")
    assert len(detail.json()["messages"]) == 1


def test_list_tickets_with_filters(client: TestClient, customer_id: int) -> None:
    _create_ticket(client, customer_id, category="billing", priority="high")
    _create_ticket(client, customer_id, subject="Bug", category="technical", priority="low")

    response = client.get("/api/tickets", params={"category": "billing"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "billing"


def test_get_missing_ticket_returns_404(client: TestClient) -> None:
    response = client.get("/api/tickets/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_ticket_validation_error(client: TestClient, customer_id: int) -> None:
    response = client.post(
        "/api/tickets",
        json={"customer_id": customer_id, "subject": "", "description": ""},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
