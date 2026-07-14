"""Business rules for tickets: creation, status transitions, messages, resolve."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.models.enums import (
    MessageAuthorType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.ticket import Ticket, TicketMessage
from app.models.user import User
from app.repositories.customer_repository import CustomerRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreate, TicketMessageCreate, TicketUpdate

# Allowed status transitions (PRD 6.3). Same-status is treated as a no-op.
_ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.new: {
        TicketStatus.open,
        TicketStatus.pending_customer,
        TicketStatus.pending_billing,
        TicketStatus.resolved,
        TicketStatus.closed,
    },
    TicketStatus.open: {
        TicketStatus.pending_customer,
        TicketStatus.pending_billing,
        TicketStatus.resolved,
        TicketStatus.closed,
    },
    TicketStatus.pending_customer: {
        TicketStatus.open,
        TicketStatus.resolved,
        TicketStatus.closed,
    },
    TicketStatus.pending_billing: {
        TicketStatus.open,
        TicketStatus.resolved,
        TicketStatus.closed,
    },
    TicketStatus.resolved: {TicketStatus.open, TicketStatus.closed},
    TicketStatus.closed: {TicketStatus.open},
}


class TicketService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TicketRepository(db)
        self.customers = CustomerRepository(db)

    def list_tickets(
        self,
        *,
        limit: int,
        offset: int,
        status: TicketStatus | None = None,
        category: TicketCategory | None = None,
        priority: TicketPriority | None = None,
        customer_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Ticket], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            status=status,
            category=category,
            priority=priority,
            customer_id=customer_id,
            search=search,
        )

    def get_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = self.repo.get_with_detail(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket

    def create_ticket(self, payload: TicketCreate) -> Ticket:
        if self.customers.get(payload.customer_id) is None:
            raise ValidationAppError(f"Customer {payload.customer_id} does not exist")

        ticket = Ticket(**payload.model_dump())
        self.repo.add(ticket)
        self.db.commit()
        return self.get_ticket(ticket.id)

    def _validate_transition(self, current: TicketStatus, target: TicketStatus) -> None:
        if current == target:
            return
        if target not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise ConflictError(
                f"Cannot transition ticket from '{current}' to '{target}'",
                details={"from": current, "to": target},
            )

    def update_ticket(self, ticket_id: uuid.UUID, payload: TicketUpdate) -> Ticket:
        ticket = self._get_or_404(ticket_id)
        data = payload.model_dump(exclude_unset=True)

        if "status" in data and data["status"] is not None:
            self._validate_transition(ticket.status, data["status"])

        for field, value in data.items():
            setattr(ticket, field, value)

        self.db.commit()
        return self.get_ticket(ticket.id)

    def resolve_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = self._get_or_404(ticket_id)
        self._validate_transition(ticket.status, TicketStatus.resolved)
        ticket.status = TicketStatus.resolved
        self.db.commit()
        return self.get_ticket(ticket.id)

    def add_message(
        self, ticket_id: uuid.UUID, payload: TicketMessageCreate, current_user: User
    ) -> TicketMessage:
        ticket = self._get_or_404(ticket_id)
        author_id = current_user.id if payload.author_type == MessageAuthorType.agent else None
        message = TicketMessage(
            ticket_id=ticket.id,
            author_type=payload.author_type,
            author_id=author_id,
            body=payload.body,
            visibility=payload.visibility,
            ai_generated=payload.ai_generated,
        )
        self.repo.add_message(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _get_or_404(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = self.repo.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket
