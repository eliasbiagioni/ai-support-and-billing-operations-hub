"""Billing API router (PRD 8, 10)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.integrations.stripe_client import StripeClient, get_stripe_client
from app.models.user import User
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerBillingSummary,
    InvoiceRead,
    PaymentRead,
)
from app.schemas.common import Page
from app.services.billing_service import BillingService

router = APIRouter(tags=["billing"])


@router.get("/customers/{customer_id}/billing", response_model=CustomerBillingSummary)
def get_customer_billing(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomerBillingSummary:
    return BillingService(db).customer_summary(customer_id)


@router.post(
    "/customers/{customer_id}/checkout-session",
    response_model=CheckoutSessionResponse,
)
def create_checkout_session(
    customer_id: uuid.UUID,
    payload: CheckoutSessionRequest | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    stripe: StripeClient = Depends(get_stripe_client),
) -> CheckoutSessionResponse:
    price_id = payload.price_id if payload else None
    return BillingService(db).create_checkout_session(
        customer_id, stripe, price_id=price_id
    )


@router.get("/invoices", response_model=Page[InvoiceRead])
def list_invoices(
    pagination: Pagination = Depends(get_pagination),
    customer_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[InvoiceRead]:
    items, total = BillingService(db).list_invoices(
        limit=pagination.limit, offset=pagination.offset, customer_id=customer_id
    )
    return Page[InvoiceRead](
        items=[InvoiceRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/payments", response_model=Page[PaymentRead])
def list_payments(
    pagination: Pagination = Depends(get_pagination),
    customer_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[PaymentRead]:
    items, total = BillingService(db).list_payments(
        limit=pagination.limit, offset=pagination.offset, customer_id=customer_id
    )
    return Page[PaymentRead](
        items=[PaymentRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
