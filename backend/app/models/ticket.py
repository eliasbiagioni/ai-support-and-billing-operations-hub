"""Ticket and ticket message models - the core support objects (PRD 9)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import (
    MessageAuthorType,
    MessageVisibility,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.user import User


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_customer_id", "customer_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_category", "category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(60), default="web", nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"), default=TicketStatus.new, nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.medium,
        nullable=False,
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category"),
        default=TicketCategory.other,
        nullable=False,
    )
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="tickets")
    assignee: Mapped[User | None] = relationship(lazy="joined")
    messages: Mapped[list[TicketMessage]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketMessage.created_at",
    )


class TicketMessage(TimestampMixin, Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_type: Mapped[MessageAuthorType] = mapped_column(
        Enum(MessageAuthorType, name="message_author_type"), nullable=False
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[MessageVisibility] = mapped_column(
        Enum(MessageVisibility, name="message_visibility"),
        default=MessageVisibility.internal,
        nullable=False,
    )
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    ticket: Mapped[Ticket] = relationship(back_populates="messages")
