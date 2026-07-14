"""Data access for AI audit logs (PRD 12: repositories layer)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_audit_log import AIAuditLog


class AIAuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, log: AIAuditLog) -> AIAuditLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list(
        self,
        *,
        limit: int,
        offset: int,
        ticket_id: uuid.UUID | None = None,
        action_type: str | None = None,
    ) -> tuple[list[AIAuditLog], int]:
        filters = []
        if ticket_id is not None:
            filters.append(AIAuditLog.ticket_id == ticket_id)
        if action_type:
            filters.append(AIAuditLog.action_type == action_type)

        count_stmt = select(func.count()).select_from(AIAuditLog)
        list_stmt = select(AIAuditLog).order_by(AIAuditLog.created_at.desc())
        for condition in filters:
            count_stmt = count_stmt.where(condition)
            list_stmt = list_stmt.where(condition)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(list_stmt.limit(limit).offset(offset)).all())
        return items, total
