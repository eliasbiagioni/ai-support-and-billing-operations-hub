"""Copilot conversation models (WebSocket persistence).

A ``Conversation`` groups the turns of a single Billing Copilot chat so the full
history can be replayed to the LLM on every new question and restored after a
refresh/reconnect. Only ``user``/``assistant`` turns are persisted; intermediate
tool round-trips are re-derived each turn.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModelMixin


class Conversation(BaseModelMixin, Base):
    __tablename__ = "copilot_conversations"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    messages: Mapped[list[ConversationMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )


class ConversationMessage(BaseModelMixin, Base):
    __tablename__ = "copilot_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Assistant-turn metadata serialized as text JSON (Postgres + SQLite).
    tools_called_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    citations_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    proposed_actions_json: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )
    risk_flags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
