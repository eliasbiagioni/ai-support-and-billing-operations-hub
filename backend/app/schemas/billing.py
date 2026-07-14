"""Pydantic schemas for billing (PRD 8, 9.1)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import InvoiceStatus, PaymentStatus


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    stripe_invoice_id: str | None
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    status: InvoiceStatus
    description: str | None
    due_date: datetime | None
    created_at: datetime


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None
    stripe_payment_intent_id: str | None
    amount: Decimal
    currency: str
    status: PaymentStatus
    failure_reason: str | None
    created_at: datetime


class CustomerBillingSummary(BaseModel):
    customer_id: uuid.UUID
    plan_name: str | None
    outstanding_balance: Decimal
    latest_invoice: InvoiceRead | None
    latest_payment: PaymentRead | None
    invoices: list[InvoiceRead]
    payments: list[PaymentRead]


class CheckoutSessionRequest(BaseModel):
    price_id: str | None = None


class CheckoutSessionResponse(BaseModel):
    id: str
    url: str


class WebhookEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    event_id: str
    event_type: str
    processed: bool
    created_at: datetime


class WebhookAck(BaseModel):
    received: bool
    processed: bool
