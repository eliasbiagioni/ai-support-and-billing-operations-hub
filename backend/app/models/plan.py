"""Billing plan model. Maps local plans to Stripe price IDs (used in later phases)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import BillingInterval


class Plan(TimestampMixin, Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Numeric (not float) for money, per PRD 9.1.
    price_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    interval: Mapped[BillingInterval] = mapped_column(
        Enum(BillingInterval, name="billing_interval"),
        default=BillingInterval.month,
        nullable=False,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_seats: Mapped[int | None] = mapped_column(Integer, nullable=True)
