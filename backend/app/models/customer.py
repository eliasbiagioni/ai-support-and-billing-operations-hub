"""Customer model - central object for tickets and billing (PRD 9)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.models.enums import CustomerStatus

if TYPE_CHECKING:
    from app.models.plan import Plan
    from app.models.ticket import Ticket


class Customer(BaseModelMixin, Base):
    __tablename__ = "customers"

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status"),
        default=CustomerStatus.active,
        nullable=False,
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped[Plan | None] = relationship(lazy="joined")
    tickets: Mapped[list[Ticket]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
