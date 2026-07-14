"""Webhook event model - dedupes provider events for idempotency (PRD 8.3)."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BaseModelMixin


class WebhookEvent(BaseModelMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_webhook_provider_event"),
    )

    provider: Mapped[str] = mapped_column(String(60), default="stripe", nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload: Mapped[str] = mapped_column(Text, default="", nullable=False)
