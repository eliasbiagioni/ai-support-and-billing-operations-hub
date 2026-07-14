"""Data access for copilot conversations and their messages (PRD 12)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID | None,
        customer_id: uuid.UUID | None = None,
        ticket_id: uuid.UUID | None = None,
        title: str = "",
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            customer_id=customer_id,
            ticket_id=ticket_id,
            title=title,
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    def list_for_user(
        self, user_id: uuid.UUID, *, limit: int, offset: int
    ) -> tuple[list[Conversation], int]:
        base = select(Conversation).where(Conversation.user_id == user_id)
        total = (
            self.db.scalar(
                select(func.count())
                .select_from(Conversation)
                .where(Conversation.user_id == user_id)
            )
            or 0
        )
        items = list(
            self.db.scalars(
                base.order_by(Conversation.updated_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return items, total

    def messages(self, conversation_id: uuid.UUID) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
        )
        return list(self.db.scalars(stmt).all())

    def add_message(
        self,
        *,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        tools_called_json: str = "[]",
        citations_json: str = "[]",
        proposed_actions_json: str = "[]",
        risk_flags_json: str = "[]",
    ) -> ConversationMessage:
        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tools_called_json=tools_called_json,
            citations_json=citations_json,
            proposed_actions_json=proposed_actions_json,
            risk_flags_json=risk_flags_json,
        )
        self.db.add(message)
        self.db.flush()
        return message
