"""AI audit log model - records every AI action for transparency (PRD 7.3)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BaseModelMixin


class AIAuditLog(BaseModelMixin, Base):
    __tablename__ = "ai_audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    input_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # JSON serialized as text for cross-dialect simplicity (Postgres + SQLite).
    output_json: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tools_called_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    risk_flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
