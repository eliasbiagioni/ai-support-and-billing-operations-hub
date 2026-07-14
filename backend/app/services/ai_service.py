"""AI Assist business logic: classify, summarize, suggest reply (PRD 7.3).

Each action calls the injected ``LLMClient`` and records an ``AIAuditLog`` row so
every AI interaction is traceable. Classification validates the model's JSON and
retries once before failing safely.
"""

from __future__ import annotations

import json
import uuid

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.prompts import classify_prompt, suggest_reply_prompt, summary_prompt
from app.core.errors import AppError, NotFoundError
from app.integrations.llm_client import LLMClient
from app.models.ai_audit_log import AIAuditLog
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.ai_repository import AIAuditRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ai import (
    SuggestedReplyResult,
    SummaryResult,
    TicketClassification,
)

_INPUT_SUMMARY_LEN = 280


class AIProcessingError(AppError):
    status_code = 502
    code = "ai_processing_error"


class AIService:
    def __init__(self, db: Session, llm: LLMClient | None = None) -> None:
        # ``llm`` is optional so read-only operations (audit log listing) can run
        # without a configured client; AI actions require it.
        self.db = db
        self.llm = llm
        self.tickets = TicketRepository(db)
        self.audit = AIAuditRepository(db)

    @property
    def _client(self) -> LLMClient:
        if self.llm is None:  # pragma: no cover - guarded by dependency wiring
            raise AIProcessingError("No LLM client configured for this operation.")
        return self.llm

    def _get_ticket(self, ticket_id: uuid.UUID) -> Ticket:
        ticket = self.tickets.get_with_detail(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket

    @staticmethod
    def _message_lines(ticket: Ticket) -> list[str]:
        lines: list[str] = []
        for message in ticket.messages:
            lines.append(f"{message.author_type}: {message.body}")
        return lines

    def _record(
        self,
        *,
        action_type: str,
        ticket: Ticket,
        current_user: User,
        output: object,
        risk_flags: list[str],
    ) -> None:
        self.audit.add(
            AIAuditLog(
                user_id=current_user.id,
                ticket_id=ticket.id,
                customer_id=ticket.customer_id,
                action_type=action_type,
                input_summary=ticket.subject[:_INPUT_SUMMARY_LEN],
                output_json=json.dumps(output),
                tools_called_json="[]",
                risk_flags_json=json.dumps(risk_flags),
                approved=False,
            )
        )
        self.db.commit()

    def classify(
        self, ticket_id: uuid.UUID, current_user: User
    ) -> TicketClassification:
        ticket = self._get_ticket(ticket_id)
        system, user = classify_prompt(ticket.subject, ticket.description)

        result = self._classify_with_retry(system, user)

        risk_flags = ["billing_lookup"] if result.billing_lookup_required else []
        self._record(
            action_type="classify",
            ticket=ticket,
            current_user=current_user,
            output=result.model_dump(mode="json"),
            risk_flags=risk_flags,
        )
        return result

    def _classify_with_retry(self, system: str, user: str) -> TicketClassification:
        last_error: Exception | None = None
        for _ in range(2):
            raw = self._client.complete(system=system, user=user, json_mode=True)
            try:
                data = json.loads(raw)
                return TicketClassification.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                # On the retry, nudge the model to fix its output.
                user = f"{user}\n\nYour previous response was invalid JSON. Return only valid JSON."
        raise AIProcessingError(
            "The AI returned an unparseable classification.",
            details={"error": str(last_error)},
        )

    def summarize(self, ticket_id: uuid.UUID, current_user: User) -> SummaryResult:
        ticket = self._get_ticket(ticket_id)
        system, user = summary_prompt(
            ticket.subject, ticket.description, self._message_lines(ticket)
        )
        text = self._client.complete(system=system, user=user).strip()
        if not text:
            raise AIProcessingError("The AI returned an empty summary.")
        result = SummaryResult(summary=text)
        self._record(
            action_type="summarize",
            ticket=ticket,
            current_user=current_user,
            output=result.model_dump(mode="json"),
            risk_flags=[],
        )
        return result

    def suggest_reply(
        self, ticket_id: uuid.UUID, current_user: User
    ) -> SuggestedReplyResult:
        ticket = self._get_ticket(ticket_id)
        system, user = suggest_reply_prompt(
            ticket.subject, ticket.description, self._message_lines(ticket)
        )
        text = self._client.complete(system=system, user=user).strip()
        if not text:
            raise AIProcessingError("The AI returned an empty reply.")
        result = SuggestedReplyResult(reply=text)
        self._record(
            action_type="suggest_reply",
            ticket=ticket,
            current_user=current_user,
            output=result.model_dump(mode="json"),
            risk_flags=["human_review_required"],
        )
        return result

    def list_audit_logs(
        self,
        *,
        limit: int,
        offset: int,
        ticket_id: uuid.UUID | None = None,
        action_type: str | None = None,
    ) -> tuple[list[AIAuditLog], int]:
        return self.audit.list(
            limit=limit, offset=offset, ticket_id=ticket_id, action_type=action_type
        )
