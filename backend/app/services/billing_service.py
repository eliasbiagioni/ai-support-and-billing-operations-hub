"""Billing business logic: checkout sessions and billing summaries (PRD 8)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError, ValidationAppError
from app.integrations.stripe_client import StripeClient
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.repositories.billing_repository import BillingRepository
from app.repositories.customer_repository import CustomerRepository
from app.schemas.billing import (
    CheckoutSessionResponse,
    CustomerBillingSummary,
    InvoiceRead,
    PaymentRead,
)


class BillingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BillingRepository(db)
        self.customers = CustomerRepository(db)

    def create_checkout_session(
        self,
        customer_id: uuid.UUID,
        stripe: StripeClient,
        *,
        price_id: str | None = None,
    ) -> CheckoutSessionResponse:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")

        resolved_price = price_id or settings.STRIPE_PRICE_ID_PRO
        if not resolved_price:
            raise ValidationAppError(
                "No Stripe price configured. Set STRIPE_PRICE_ID_PRO or pass price_id."
            )

        session = stripe.create_checkout_session(
            price_id=resolved_price,
            success_url=f"{settings.FRONTEND_URL}/billing?checkout=success",
            cancel_url=f"{settings.FRONTEND_URL}/billing?checkout=cancelled",
            customer_email=customer.email,
            metadata={
                "customer_id": str(customer.id),
                "plan_id": str(customer.plan_id) if customer.plan_id else "",
            },
        )
        return CheckoutSessionResponse(id=session["id"], url=session["url"])

    def list_invoices(
        self, *, limit: int, offset: int, customer_id: uuid.UUID | None = None
    ) -> tuple[list[Invoice], int]:
        return self.repo.list_invoices(
            limit=limit, offset=offset, customer_id=customer_id
        )

    def list_payments(
        self, *, limit: int, offset: int, customer_id: uuid.UUID | None = None
    ) -> tuple[list[Payment], int]:
        return self.repo.list_payments(
            limit=limit, offset=offset, customer_id=customer_id
        )

    def customer_summary(self, customer_id: uuid.UUID) -> CustomerBillingSummary:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")

        invoices, _ = self.repo.list_invoices(
            limit=100, offset=0, customer_id=customer_id
        )
        payments, _ = self.repo.list_payments(
            limit=100, offset=0, customer_id=customer_id
        )

        outstanding = sum(
            (inv.amount_due - inv.amount_paid for inv in invoices),
            Decimal("0"),
        )
        outstanding = max(outstanding, Decimal("0"))

        return CustomerBillingSummary(
            customer_id=customer.id,
            plan_name=customer.plan.name if customer.plan else None,
            outstanding_balance=outstanding,
            latest_invoice=InvoiceRead.model_validate(invoices[0]) if invoices else None,
            latest_payment=PaymentRead.model_validate(payments[0]) if payments else None,
            invoices=[InvoiceRead.model_validate(inv) for inv in invoices],
            payments=[PaymentRead.model_validate(pay) for pay in payments],
        )
