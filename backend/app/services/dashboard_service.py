"""Dashboard summary metrics (PRD 5.2 cards)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.ticket import Ticket
from app.schemas.ticket import DashboardSummary

_UNRESOLVED = (TicketStatus.resolved, TicketStatus.closed)
_HIGH_PRIORITY = (TicketPriority.high, TicketPriority.urgent)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _count(self, *conditions: object) -> int:
        stmt = select(func.count()).select_from(Ticket)
        for condition in conditions:
            stmt = stmt.where(condition)
        return self.db.scalar(stmt) or 0

    def summary(self) -> DashboardSummary:
        total_customers = self.db.scalar(select(func.count()).select_from(Customer)) or 0
        return DashboardSummary(
            open_tickets=self._count(Ticket.status == TicketStatus.open),
            high_priority_tickets=self._count(Ticket.priority.in_(_HIGH_PRIORITY)),
            billing_tickets=self._count(Ticket.category == TicketCategory.billing),
            unresolved_tickets=self._count(Ticket.status.notin_(_UNRESOLVED)),
            total_customers=total_customers,
        )
