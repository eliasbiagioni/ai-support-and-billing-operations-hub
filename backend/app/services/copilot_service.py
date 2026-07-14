"""AI Billing Copilot: a tool-calling agent over billing + knowledge (Phase 5).

Runs a bounded tool loop: the model calls read-only tools for facts and
``propose_*`` tools to queue risky actions for human approval. Every run writes
an ``AIAuditLog`` row (action_type="copilot") capturing the tools used and any
risk flags, keeping AI actions transparent (PRD 7.3).

``run`` serves the stateless HTTP endpoint (single turn); ``run_turn`` serves the
WebSocket copilot, replaying the persisted conversation so the model has the full
context to continue the conversation.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai.guardrails import apply_input_guardrails
from app.ai.prompts import COPILOT_SYSTEM, copilot_context
from app.ai.tools import CopilotTools
from app.core.errors import AppError
from app.integrations.llm_client import LLMClient
from app.models.ai_audit_log import AIAuditLog
from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User
from app.repositories.ai_repository import AIAuditRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.ai import CopilotRequest, CopilotResponse

_MAX_ITERATIONS = 5
_INPUT_SUMMARY_LEN = 280
_TITLE_LEN = 80

ToolCallback = Callable[[str], None]


class CopilotError(AppError):
    status_code = 502
    code = "copilot_error"


class CopilotService:
    def __init__(self, db: Session, llm: LLMClient | None = None) -> None:
        self.db = db
        self.llm = llm
        self.audit = AIAuditRepository(db)
        self.conversations = ConversationRepository(db)

    @property
    def _client(self) -> LLMClient:
        if self.llm is None:  # pragma: no cover - guarded by dependency wiring
            raise CopilotError("No LLM client configured for the copilot.")
        return self.llm

    # -- Shared tool loop ------------------------------------------------------
    def _run_loop(
        self,
        messages: list[dict[str, Any]],
        tools: CopilotTools,
        on_tool: ToolCallback | None = None,
    ) -> str:
        answer = ""
        for _ in range(_MAX_ITERATIONS):
            result = self._client.chat(messages=messages, tools=tools.specs())
            messages.append(result.as_assistant_message())
            if not result.tool_calls:
                answer = (result.content or "").strip()
                break
            for call in result.tool_calls:
                if on_tool is not None:
                    on_tool(call.name)
                output = tools.execute(call.name, call.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(output),
                    }
                )
        else:
            answer = "I could not complete that request within the allowed steps."
        return answer or "I don't have enough information to answer that."

    @staticmethod
    def _risk_flags(input_flags: list[str], tools: CopilotTools) -> list[str]:
        flags: list[str] = list(dict.fromkeys(input_flags))
        if tools.proposed_actions:
            flags.append("proposed_action")
        return flags

    # -- Stateless HTTP entry point -------------------------------------------
    def run(self, request: CopilotRequest, current_user: User) -> CopilotResponse:
        tools = CopilotTools(self.db, current_user)
        messages: list[dict[str, Any]] = [{"role": "system", "content": COPILOT_SYSTEM}]
        context = copilot_context(
            str(request.customer_id) if request.customer_id else None,
            str(request.ticket_id) if request.ticket_id else None,
        )
        if context:
            messages.append({"role": "system", "content": context})
        safe_message, input_flags = apply_input_guardrails(request.message)
        messages.append({"role": "user", "content": safe_message})

        answer = self._run_loop(messages, tools)
        response = CopilotResponse(
            answer=answer,
            tools_called=tools.called,
            citations=tools.citations,
            proposed_actions=tools.proposed_actions,
            risk_flags=self._risk_flags(input_flags, tools),
        )
        self._record(
            current_user,
            response,
            ticket_id=request.ticket_id,
            customer_id=request.customer_id,
            input_summary=safe_message,
        )
        self.db.commit()
        return response

    # -- WebSocket entry point (full-history conversation) --------------------
    def run_turn(
        self,
        *,
        conversation: Conversation,
        user_message: str,
        current_user: User,
        on_tool: ToolCallback | None = None,
    ) -> tuple[CopilotResponse, ConversationMessage]:
        tools = CopilotTools(self.db, current_user)
        safe_message, input_flags = apply_input_guardrails(user_message)

        messages: list[dict[str, Any]] = [{"role": "system", "content": COPILOT_SYSTEM}]
        context = copilot_context(
            str(conversation.customer_id) if conversation.customer_id else None,
            str(conversation.ticket_id) if conversation.ticket_id else None,
        )
        if context:
            messages.append({"role": "system", "content": context})
        # Replay the full prior conversation so the model has complete context.
        for prior in self.conversations.messages(conversation.id):
            messages.append({"role": prior.role, "content": prior.content})
        messages.append({"role": "user", "content": safe_message})

        # Persist the user turn before running so a mid-turn failure keeps it.
        self.conversations.add_message(
            conversation_id=conversation.id, role="user", content=safe_message
        )

        answer = self._run_loop(messages, tools, on_tool=on_tool)
        response = CopilotResponse(
            answer=answer,
            tools_called=tools.called,
            citations=tools.citations,
            proposed_actions=tools.proposed_actions,
            risk_flags=self._risk_flags(input_flags, tools),
        )

        assistant_message = self.conversations.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.answer,
            tools_called_json=json.dumps(response.tools_called),
            citations_json=json.dumps(
                [c.model_dump(mode="json") for c in response.citations]
            ),
            proposed_actions_json=json.dumps(
                [a.model_dump(mode="json") for a in response.proposed_actions]
            ),
            risk_flags_json=json.dumps(response.risk_flags),
        )

        if not conversation.title:
            conversation.title = safe_message[:_TITLE_LEN]
        conversation.updated_at = datetime.now(UTC)

        self._record(
            current_user,
            response,
            ticket_id=conversation.ticket_id,
            customer_id=conversation.customer_id,
            input_summary=safe_message,
        )
        self.db.commit()
        self.db.refresh(assistant_message)
        return response, assistant_message

    def _record(
        self,
        current_user: User,
        response: CopilotResponse,
        *,
        ticket_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
        input_summary: str,
    ) -> None:
        self.audit.add(
            AIAuditLog(
                user_id=current_user.id,
                ticket_id=ticket_id,
                customer_id=customer_id,
                action_type="copilot",
                input_summary=input_summary[:_INPUT_SUMMARY_LEN],
                output_json=json.dumps(response.model_dump(mode="json")),
                tools_called_json=json.dumps(response.tools_called),
                risk_flags_json=json.dumps(response.risk_flags),
                approved=False,
            )
        )
