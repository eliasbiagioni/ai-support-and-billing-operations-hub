"""AI Assist + RAG copilot API router (PRD 10, Phases 3/5/6)."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.rate_limit import limiter
from app.core.security import JWTError, decode_access_token
from app.db.session import get_db
from app.integrations.llm_client import LLMClient, get_llm_client
from app.models.ai_audit_log import AIAuditLog
from app.models.conversation import ConversationMessage
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.ai import (
    AIAuditLogRead,
    Citation,
    ConversationDetail,
    ConversationMessageRead,
    ConversationRead,
    CopilotRequest,
    CopilotResponse,
    ProposedAction,
    SuggestedReplyResult,
    SummaryResult,
    TicketClassification,
)
from app.schemas.common import Page
from app.services.ai_service import AIService
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/ai", tags=["ai"])

_WS_AUTH_CLOSE = 4401


def _load_json(raw: str, fallback: object) -> object:
    try:
        return json.loads(raw) if raw else fallback
    except json.JSONDecodeError:
        return fallback


def _to_message_read(message: ConversationMessage) -> ConversationMessageRead:
    return ConversationMessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        tools_called=list(_load_json(message.tools_called_json, [])),  # type: ignore[arg-type]
        citations=[
            Citation.model_validate(c)
            for c in _load_json(message.citations_json, [])  # type: ignore[union-attr]
        ],
        proposed_actions=[
            ProposedAction.model_validate(a)
            for a in _load_json(message.proposed_actions_json, [])  # type: ignore[union-attr]
        ],
        risk_flags=list(_load_json(message.risk_flags_json, [])),  # type: ignore[arg-type]
        created_at=message.created_at,
    )


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
@limiter.limit(settings.RATE_LIMIT_AI)
def classify_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> TicketClassification:
    return AIService(db, llm).classify(ticket_id, current_user)


@router.post("/tickets/{ticket_id}/summarize", response_model=SummaryResult)
@limiter.limit(settings.RATE_LIMIT_AI)
def summarize_ticket(
    request: Request,
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> SummaryResult:
    return AIService(db, llm).summarize(ticket_id, current_user)


@router.post("/tickets/{ticket_id}/suggest-reply", response_model=SuggestedReplyResult)
@limiter.limit(settings.RATE_LIMIT_AI)
def suggest_reply(
    request: Request,
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> SuggestedReplyResult:
    return AIService(db, llm).suggest_reply(ticket_id, current_user)


@router.post("/copilot", response_model=CopilotResponse)
@limiter.limit(settings.RATE_LIMIT_AI)
def run_copilot(
    request: Request,
    payload: CopilotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: LLMClient = Depends(get_llm_client),
) -> CopilotResponse:
    return CopilotService(db, llm).run(payload, current_user)


@router.get("/conversations", response_model=Page[ConversationRead])
def list_conversations(
    pagination: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Page[ConversationRead]:
    repo = ConversationRepository(db)
    items, total = repo.list_for_user(
        current_user.id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[ConversationRead](
        items=[ConversationRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationDetail:
    repo = ConversationRepository(db)
    conversation = repo.get(conversation_id)
    if conversation is None or conversation.user_id != current_user.id:
        raise NotFoundError("Conversation not found.")
    messages = repo.messages(conversation_id)
    return ConversationDetail(
        **ConversationRead.model_validate(conversation).model_dump(),
        messages=[_to_message_read(message) for message in messages],
    )


def _authenticate_ws(websocket: WebSocket, db: Session) -> User | None:
    """Resolve the JWT from the ``token`` query param (browsers cannot set the
    Authorization header on a WebSocket). Returns the active user or ``None``."""

    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (JWTError, ValueError, TypeError):
        return None
    user = db.get(User, user_id)
    if user is None or not user.active:
        return None
    return user


def _resolve_conversation(
    repo: ConversationRepository, websocket: WebSocket, user: User
):
    """Load the requested conversation (if owned by the user) or start a new one."""

    raw_id = websocket.query_params.get("conversation_id")
    if raw_id:
        try:
            conversation = repo.get(uuid.UUID(raw_id))
        except (ValueError, TypeError):
            conversation = None
        if conversation is not None and conversation.user_id == user.id:
            return conversation

    customer_id: uuid.UUID | None = None
    raw_customer = websocket.query_params.get("customer_id")
    if raw_customer:
        try:
            customer_id = uuid.UUID(raw_customer)
        except (ValueError, TypeError):
            customer_id = None
    return repo.create(user_id=user.id, customer_id=customer_id)


@router.websocket("/copilot/ws")
async def copilot_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    await websocket.accept()

    user = _authenticate_ws(websocket, db)
    if user is None:
        await websocket.close(code=_WS_AUTH_CLOSE)
        return

    # Resolve the LLM through the app's dependency overrides so tests can inject
    # a fake; falls back to the configured client in production.
    llm_factory = websocket.app.dependency_overrides.get(
        get_llm_client, get_llm_client
    )
    try:
        llm = llm_factory()
    except Exception:  # noqa: BLE001 - surface config problems to the client
        await websocket.send_json(
            {"type": "error", "message": "AI is not configured on this server."}
        )
        await websocket.close()
        return

    repo = ConversationRepository(db)
    conversation = _resolve_conversation(repo, websocket, user)
    db.commit()

    await websocket.send_json(
        {
            "type": "ready",
            "conversation_id": str(conversation.id),
            "customer_id": str(conversation.customer_id)
            if conversation.customer_id
            else None,
            "history": [
                _to_message_read(m).model_dump(mode="json")
                for m in repo.messages(conversation.id)
            ],
        }
    )

    service = CopilotService(db, llm)
    loop = asyncio.get_running_loop()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message") if isinstance(data, dict) else None
            if not isinstance(message, str) or not message.strip():
                await websocket.send_json(
                    {"type": "error", "message": "A non-empty message is required."}
                )
                continue

            def _emit_tool(name: str) -> None:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "tool_activity", "tool": name}), loop
                )

            try:
                response, assistant = await run_in_threadpool(
                    service.run_turn,
                    conversation=conversation,
                    user_message=message,
                    current_user=user,
                    on_tool=_emit_tool,
                )
            except Exception:  # noqa: BLE001 - keep the socket open on turn errors
                db.rollback()
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "The copilot failed to answer. Please try again.",
                    }
                )
                continue

            await websocket.send_json(
                {
                    "type": "answer",
                    "message_id": str(assistant.id),
                    "created_at": assistant.created_at.isoformat(),
                    **response.model_dump(mode="json"),
                }
            )
    except WebSocketDisconnect:
        return


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
