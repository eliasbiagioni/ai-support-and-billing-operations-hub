"""Customer CRUD and validation tests (PRD 14.1)."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_create_and_get_customer(client: TestClient) -> None:
    create = client.post(
        "/api/customers",
        json={
            "company_name": "Northwind",
            "email": "hello@northwind.example",
            "contact_name": "Grace",
        },
    )
    assert create.status_code == 201, create.text
    created = create.json()
    assert created["company_name"] == "Northwind"
    assert created["status"] == "active"

    fetched = client.get(f"/api/customers/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "hello@northwind.example"


def test_list_customers_pagination(client: TestClient) -> None:
    for i in range(3):
        client.post(
            "/api/customers",
            json={"company_name": f"Co {i}", "email": f"co{i}@example.com"},
        )
    response = client.get("/api/customers", params={"limit": 2, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2


def test_update_customer(client: TestClient, customer_id: str) -> None:
    response = client.patch(
        f"/api/customers/{customer_id}",
        json={"status": "suspended", "notes": "Payment failed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "suspended"
    assert body["notes"] == "Payment failed"


def test_get_missing_customer_returns_404(client: TestClient) -> None:
    response = client.get(f"/api/customers/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_create_customer_invalid_email(client: TestClient) -> None:
    response = client.post(
        "/api/customers",
        json={"company_name": "Bad", "email": "not-an-email"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
