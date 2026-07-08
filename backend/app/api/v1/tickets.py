"""Tickets API router (PRD 10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.enums import TicketCategory, TicketPriority, TicketStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.ticket import (
    TicketCreate,
    TicketDetail,
    TicketMessageCreate,
    TicketMessageRead,
    TicketRead,
    TicketUpdate,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=Page[TicketRead])
def list_tickets(
    pagination: Pagination = Depends(get_pagination),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    category: TicketCategory | None = Query(default=None),
    priority: TicketPriority | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    q: str | None = Query(default=None, description="Search in subject"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[TicketRead]:
    items, total = TicketService(db).list_tickets(
        limit=pagination.limit,
        offset=pagination.offset,
        status=status_filter,
        category=category,
        priority=priority,
        customer_id=customer_id,
        search=q,
    )
    return Page[TicketRead](
        items=[TicketRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("", response_model=TicketDetail, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TicketDetail:
    ticket = TicketService(db).create_ticket(payload)
    return TicketDetail.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TicketDetail:
    ticket = TicketService(db).get_ticket(ticket_id)
    return TicketDetail.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketDetail)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TicketDetail:
    ticket = TicketService(db).update_ticket(ticket_id, payload)
    return TicketDetail.model_validate(ticket)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageRead,
    status_code=status.HTTP_201_CREATED,
)
def add_ticket_message(
    ticket_id: int,
    payload: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketMessageRead:
    message = TicketService(db).add_message(ticket_id, payload, current_user)
    return TicketMessageRead.model_validate(message)


@router.post("/{ticket_id}/resolve", response_model=TicketDetail)
def resolve_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TicketDetail:
    ticket = TicketService(db).resolve_ticket(ticket_id)
    return TicketDetail.model_validate(ticket)
