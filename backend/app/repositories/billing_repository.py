"""Data access for invoices, payments, and webhook events (PRD 12)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent


class BillingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # Invoices -----------------------------------------------------------------
    def add_invoice(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def get_invoice_by_stripe_id(self, stripe_invoice_id: str) -> Invoice | None:
        return self.db.scalars(
            select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice_id)
        ).first()

    def list_invoices(
        self, *, limit: int, offset: int, customer_id: uuid.UUID | None = None
    ) -> tuple[list[Invoice], int]:
        count_stmt = select(func.count()).select_from(Invoice)
        list_stmt = select(Invoice).order_by(Invoice.created_at.desc())
        if customer_id is not None:
            count_stmt = count_stmt.where(Invoice.customer_id == customer_id)
            list_stmt = list_stmt.where(Invoice.customer_id == customer_id)
        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(list_stmt.limit(limit).offset(offset)).all())
        return items, total

    # Payments -----------------------------------------------------------------
    def add_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    def get_payment_by_intent(self, intent_id: str) -> Payment | None:
        return self.db.scalars(
            select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
        ).first()

    def list_payments(
        self, *, limit: int, offset: int, customer_id: uuid.UUID | None = None
    ) -> tuple[list[Payment], int]:
        count_stmt = select(func.count()).select_from(Payment)
        list_stmt = select(Payment).order_by(Payment.created_at.desc())
        if customer_id is not None:
            count_stmt = count_stmt.where(Payment.customer_id == customer_id)
            list_stmt = list_stmt.where(Payment.customer_id == customer_id)
        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(list_stmt.limit(limit).offset(offset)).all())
        return items, total

    # Webhook events -----------------------------------------------------------
    def get_event(self, provider: str, event_id: str) -> WebhookEvent | None:
        return self.db.scalars(
            select(WebhookEvent).where(
                WebhookEvent.provider == provider,
                WebhookEvent.event_id == event_id,
            )
        ).first()

    def add_event(self, event: WebhookEvent) -> WebhookEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def list_events(
        self, *, limit: int, offset: int
    ) -> tuple[list[WebhookEvent], int]:
        total = self.db.scalar(select(func.count()).select_from(WebhookEvent)) or 0
        items = list(
            self.db.scalars(
                select(WebhookEvent)
                .order_by(WebhookEvent.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return items, total
