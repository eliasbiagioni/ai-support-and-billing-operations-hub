"""Customer model - central object for tickets and billing (PRD 9)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import CustomerStatus

if TYPE_CHECKING:
    from app.models.plan import Plan
    from app.models.ticket import Ticket


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status"),
        default=CustomerStatus.active,
        nullable=False,
    )
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped[Plan | None] = relationship(lazy="joined")
    tickets: Mapped[list[Ticket]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
