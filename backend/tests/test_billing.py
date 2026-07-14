"""Billing tests with a fake Stripe client (no network, no real signatures)."""

from __future__ import annotations

import json
from typing import Any

from app.integrations.stripe_client import StripeClient, get_stripe_client
from app.main import app
from fastapi.testclient import TestClient


class FakeStripe:
    """Deterministic Stripe stand-in.

    ``construct_event`` treats the raw body as an already-verified event, which
    lets tests drive webhook processing without real signatures.
    """

    def __init__(self) -> None:
        self.sessions_created = 0

    def create_checkout_session(
        self,
        *,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None,
        metadata: dict[str, str],
    ) -> dict[str, Any]:
        self.sessions_created += 1
        return {
            "id": "cs_test_123",
            "url": "https://checkout.stripe.test/pay/cs_test_123",
        }

    def construct_event(self, *, payload: bytes, signature: str) -> dict[str, Any]:
        return json.loads(payload)


def _use_stripe(fake: StripeClient) -> None:
    app.dependency_overrides[get_stripe_client] = lambda: fake


def _post_event(client: TestClient, event: dict[str, Any]):
    return client.post(
        "/api/webhooks/stripe",
        content=json.dumps(event),
        headers={"Stripe-Signature": "test", "Content-Type": "application/json"},
    )


def test_create_checkout_session(client: TestClient, customer_id: str) -> None:
    fake = FakeStripe()
    _use_stripe(fake)
    response = client.post(
        f"/api/customers/{customer_id}/checkout-session",
        json={"price_id": "price_test_pro"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == "cs_test_123"
    assert body["url"].startswith("https://checkout.stripe.test")
    assert fake.sessions_created == 1


def test_payment_succeeded_webhook_creates_payment(
    client: TestClient, customer_id: str
) -> None:
    _use_stripe(FakeStripe())
    event = {
        "id": "evt_1",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_1",
                "amount": 9900,
                "currency": "usd",
                "metadata": {"customer_id": customer_id},
            }
        },
    }
    response = _post_event(client, event)
    assert response.status_code == 200, response.text
    assert response.json() == {"received": True, "processed": True}

    payments = client.get("/api/payments", params={"customer_id": customer_id})
    body = payments.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "succeeded"
    assert body["items"][0]["amount"] == "99.00"


def test_webhook_is_idempotent(client: TestClient, customer_id: str) -> None:
    _use_stripe(FakeStripe())
    event = {
        "id": "evt_dup",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_dup",
                "amount": 5000,
                "currency": "usd",
                "metadata": {"customer_id": customer_id},
            }
        },
    }
    first = _post_event(client, event)
    second = _post_event(client, event)
    assert first.json()["processed"] is True
    assert second.json()["processed"] is False

    payments = client.get("/api/payments", params={"customer_id": customer_id})
    assert payments.json()["total"] == 1


def test_payment_failed_webhook(client: TestClient, customer_id: str) -> None:
    _use_stripe(FakeStripe())
    event = {
        "id": "evt_fail",
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_fail",
                "amount": 2900,
                "currency": "usd",
                "metadata": {"customer_id": customer_id},
                "last_payment_error": {"message": "Your card was declined."},
            }
        },
    }
    response = _post_event(client, event)
    assert response.status_code == 200
    payments = client.get("/api/payments", params={"customer_id": customer_id})
    item = payments.json()["items"][0]
    assert item["status"] == "failed"
    assert item["failure_reason"] == "Your card was declined."


def test_customer_billing_summary(client: TestClient, customer_id: str) -> None:
    _use_stripe(FakeStripe())
    event = {
        "id": "evt_summary",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "amount_total": 9900,
                "currency": "usd",
                "invoice": "in_test_1",
                "metadata": {"customer_id": customer_id},
            }
        },
    }
    _post_event(client, event)

    summary = client.get(f"/api/customers/{customer_id}/billing")
    assert summary.status_code == 200
    body = summary.json()
    assert body["customer_id"] == customer_id
    assert len(body["invoices"]) == 1
    assert body["latest_invoice"]["status"] == "paid"
