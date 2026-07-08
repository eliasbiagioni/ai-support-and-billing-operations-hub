"""Data access for tickets and ticket messages (PRD 12: repositories layer)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.ticket import Ticket, TicketMessage


class TicketRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def get_with_detail(self, ticket_id: int) -> Ticket | None:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.messages), selectinload(Ticket.customer))
        )
        return self.db.scalars(stmt).first()

    def list(
        self,
        *,
        limit: int,
        offset: int,
        status: TicketStatus | None = None,
        category: TicketCategory | None = None,
        priority: TicketPriority | None = None,
        customer_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Ticket], int]:
        filters = []
        if status is not None:
            filters.append(Ticket.status == status)
        if category is not None:
            filters.append(Ticket.category == category)
        if priority is not None:
            filters.append(Ticket.priority == priority)
        if customer_id is not None:
            filters.append(Ticket.customer_id == customer_id)
        if search:
            filters.append(Ticket.subject.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(Ticket)
        list_stmt = select(Ticket).order_by(Ticket.created_at.desc())
        for condition in filters:
            count_stmt = count_stmt.where(condition)
            list_stmt = list_stmt.where(condition)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(list_stmt.limit(limit).offset(offset)).all())
        return items, total

    def add(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.flush()
        return ticket

    def add_message(self, message: TicketMessage) -> TicketMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def count_where(self, *conditions: object) -> int:
        stmt = select(func.count()).select_from(Ticket)
        for condition in conditions:
            stmt = stmt.where(condition)
        return self.db.scalar(stmt) or 0
