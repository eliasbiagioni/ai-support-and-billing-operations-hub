"""Pydantic schemas for AI Assist (PRD 7.3)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TicketCategory, TicketPriority


class Sentiment:
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class TicketClassification(BaseModel):
    """Structured classification output validated from the model's JSON (PRD 7.3)."""

    category: TicketCategory
    urgency: TicketPriority
    sentiment: str = Field(default="neutral")
    billing_lookup_required: bool = False
    suggested_team: str = Field(default="support", max_length=120)
    reasoning_summary: str = Field(default="", max_length=500)

    @field_validator("sentiment")
    @classmethod
    def _valid_sentiment(cls, value: str) -> str:
        allowed = {"positive", "neutral", "negative"}
        normalized = (value or "neutral").strip().lower()
        return normalized if normalized in allowed else "neutral"


class SummaryResult(BaseModel):
    summary: str


class SuggestedReplyResult(BaseModel):
    reply: str


class AIAuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    ticket_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    action_type: str
    input_summary: str
    output: Any = None
    tools_called: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    approved: bool
    created_at: datetime
