"""AI Assist API router (PRD 10). RAG/copilot are deferred to phases 5-6."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.integrations.llm_client import LLMClient, get_llm_client
from app.models.ai_audit_log import AIAuditLog
from app.models.user import User
from app.schemas.ai import (
    AIAuditLogRead,
    SuggestedReplyResult,
    SummaryResult,
    TicketClassification,
)
from app.schemas.common import Page
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


def _load_json(raw: str, fallback: object) -> object:
    try:
        return json.loads(raw) if raw else fallback
    except json.JSONDecodeError:
        return fallback


def _to_audit_read(log: AIAuditLog) -> AIAuditLogRead:
    return AIAuditLogRead(
        id=log.id,
        user_id=log.user_id,
        ticket_id=log.ticket_id,
        customer_id=log.customer_id,
        action_type=log.action_type,
        input_summary=log.input_summary,
        output=_load_json(log.output_json, None),
        tools_called=list(_load_json(log.tools_called_json, [])),  # type: ignore[arg-type]
        risk_flags=list(_load_json(log.risk_flags_json, [])),  # type: ignore[arg-type]
        approved=log.approved,
        created_at=log.created_at,
    )


@router.post("/tickets/{ticket_id}/classify", response_model=TicketClassification)
def classify_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> TicketClassification:
    return AIService(db, llm).classify(ticket_id, current_user)


@router.post("/tickets/{ticket_id}/summarize", response_model=SummaryResult)
def summarize_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> SummaryResult:
    return AIService(db, llm).summarize(ticket_id, current_user)


@router.post("/tickets/{ticket_id}/suggest-reply", response_model=SuggestedReplyResult)
def suggest_reply(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> SuggestedReplyResult:
    return AIService(db, llm).suggest_reply(ticket_id, current_user)


@router.get("/audit-logs", response_model=Page[AIAuditLogRead])
def list_audit_logs(
    pagination: Pagination = Depends(get_pagination),
    ticket_id: uuid.UUID | None = Query(default=None),
    action_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[AIAuditLogRead]:
    # LLM not needed for reads; a service without a client is fine here.
    service = AIService(db)
    items, total = service.list_audit_logs(
        limit=pagination.limit,
        offset=pagination.offset,
        ticket_id=ticket_id,
        action_type=action_type,
    )
    return Page[AIAuditLogRead](
        items=[_to_audit_read(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
