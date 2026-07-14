"""Idempotent Stripe webhook processing (PRD 8.3).

The signature is verified via the injected ``StripeClient``. Each event is stored
exactly once (unique provider+event_id); already-processed events are skipped so
retries from Stripe are safe.
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.integrations.stripe_client import StripeClient
from app.models.enums import InvoiceStatus, PaymentStatus
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent
from app.repositories.billing_repository import BillingRepository

logger = get_logger(__name__)

_PROVIDER = "stripe"


def _to_decimal(amount_cents: Any) -> Decimal:
    try:
        return Decimal(int(amount_cents)) / Decimal(100)
    except (TypeError, ValueError):
        return Decimal("0")


def _customer_id(metadata: dict[str, Any]) -> uuid.UUID | None:
    raw = metadata.get("customer_id") if metadata else None
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError:
        return None


class WebhookService:
    def __init__(self, db: Session, stripe: StripeClient) -> None:
        self.db = db
        self.stripe = stripe
        self.repo = BillingRepository(db)

    def process(self, *, payload: bytes, signature: str) -> bool:
        """Verify, store, and handle an event. Returns True if newly processed."""

        event = self.stripe.construct_event(payload=payload, signature=signature)
        event_id = str(event.get("id", ""))
        event_type = str(event.get("type", ""))

        existing = self.repo.get_event(_PROVIDER, event_id)
        if existing is not None and existing.processed:
            logger.info("Webhook %s already processed; skipping.", event_id)
            return False

        if existing is None:
            existing = self.repo.add_event(
                WebhookEvent(
                    provider=_PROVIDER,
                    event_id=event_id,
                    event_type=event_type,
                    processed=False,
                    payload=json.dumps(event.get("data", {})),
                )
            )

        data_object = (event.get("data") or {}).get("object") or {}
        self._dispatch(event_type, data_object)

        existing.processed = True
        self.db.commit()
        return True

    def _dispatch(self, event_type: str, obj: dict[str, Any]) -> None:
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
        }
        handler = handlers.get(event_type)
        if handler is None:
            logger.info("Unhandled webhook event type: %s", event_type)
            return
        handler(obj)

    def _handle_checkout_completed(self, obj: dict[str, Any]) -> None:
        metadata = obj.get("metadata") or {}
        customer_id = _customer_id(metadata)
        if customer_id is None:
            return
        amount = _to_decimal(obj.get("amount_total"))
        invoice = Invoice(
            customer_id=customer_id,
            stripe_invoice_id=obj.get("invoice"),
            amount_due=amount,
            amount_paid=amount,
            currency=str(obj.get("currency", "usd")),
            status=InvoiceStatus.paid,
            description="Checkout session completed",
        )
        self.repo.add_invoice(invoice)

    def _handle_payment_succeeded(self, obj: dict[str, Any]) -> None:
        metadata = obj.get("metadata") or {}
        customer_id = _customer_id(metadata)
        intent_id = str(obj.get("id", "")) or None
        if customer_id is None or intent_id is None:
            return
        existing = self.repo.get_payment_by_intent(intent_id)
        if existing is not None:
            existing.status = PaymentStatus.succeeded
            return
        self.repo.add_payment(
            Payment(
                customer_id=customer_id,
                stripe_payment_intent_id=intent_id,
                amount=_to_decimal(obj.get("amount")),
                currency=str(obj.get("currency", "usd")),
                status=PaymentStatus.succeeded,
            )
        )

    def _handle_payment_failed(self, obj: dict[str, Any]) -> None:
        metadata = obj.get("metadata") or {}
        customer_id = _customer_id(metadata)
        intent_id = str(obj.get("id", "")) or None
        if customer_id is None or intent_id is None:
            return
        reason = None
        error = obj.get("last_payment_error") or {}
        if isinstance(error, dict):
            reason = error.get("message")
        existing = self.repo.get_payment_by_intent(intent_id)
        if existing is not None:
            existing.status = PaymentStatus.failed
            existing.failure_reason = reason
            return
        self.repo.add_payment(
            Payment(
                customer_id=customer_id,
                stripe_payment_intent_id=intent_id,
                amount=_to_decimal(obj.get("amount")),
                currency=str(obj.get("currency", "usd")),
                status=PaymentStatus.failed,
                failure_reason=reason,
            )
        )
