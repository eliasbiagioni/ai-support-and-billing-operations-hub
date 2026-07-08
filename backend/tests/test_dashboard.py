"""Dashboard summary tests (PRD 5.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_dashboard_summary_counts(client: TestClient, customer_id: int) -> None:
    client.post(
        "/api/tickets",
        json={
            "customer_id": customer_id,
            "subject": "Billing issue",
            "description": "Charge problem",
            "category": "billing",
            "priority": "urgent",
            "status": "open",
        },
    )
    client.post(
        "/api/tickets",
        json={
            "customer_id": customer_id,
            "subject": "Tech issue",
            "description": "Crash",
            "category": "technical",
            "priority": "low",
            "status": "new",
        },
    )

    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["open_tickets"] == 1
    assert body["high_priority_tickets"] == 1
    assert body["billing_tickets"] == 1
    assert body["unresolved_tickets"] == 2
    assert body["total_customers"] == 1
