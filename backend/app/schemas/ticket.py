"""Pydantic schemas for tickets, messages, and the dashboard summary (PRD 6.3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    MessageAuthorType,
    MessageVisibility,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class TicketMessageCreate(BaseModel):
    body: str = Field(min_length=1)
    author_type: MessageAuthorType = MessageAuthorType.agent
    visibility: MessageVisibility = MessageVisibility.internal
    ai_generated: bool = False


class TicketMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_type: MessageAuthorType
    author_id: int | None
    body: str
    visibility: MessageVisibility
    ai_generated: bool
    approved_by: int | None
    created_at: datetime


class TicketCreate(BaseModel):
    customer_id: int
    subject: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    source: str = Field(default="web", max_length=60)
    category: TicketCategory = TicketCategory.other
    priority: TicketPriority = TicketPriority.medium
    status: TicketStatus = TicketStatus.new
    assigned_to: int | None = None


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    assigned_to: int | None = None


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    email: str
    status: str


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    subject: str
    description: str
    source: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    assigned_to: int | None
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketRead):
    customer: CustomerSummary | None = None
    messages: list[TicketMessageRead] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    open_tickets: int
    high_priority_tickets: int
    billing_tickets: int
    unresolved_tickets: int
    total_customers: int
