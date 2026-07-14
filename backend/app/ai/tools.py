"""Copilot tool registry (Phase 5).

Wraps existing services as read-only tools the LLM can call, plus ``propose_*``
tools that queue risky/write actions for human approval instead of executing
them. Tool results are JSON-serializable dicts fed back to the model; citations
and proposed actions are collected as side outputs for the API response.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.customer_repository import CustomerRepository
from app.schemas.ai import Citation, ProposedAction
from app.schemas.billing import InvoiceRead, PaymentRead
from app.services.billing_service import BillingService
from app.services.knowledge_service import KnowledgeService

_SNIPPET_LEN = 240


def _parse_uuid(value: Any) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


class CopilotTools:
    """Executable tool set bound to a DB session and the current user."""

    def __init__(self, db: Session, current_user: User) -> None:
        self.db = db
        self.current_user = current_user
        self.billing = BillingService(db)
        self.knowledge = KnowledgeService(db)
        self.customers = CustomerRepository(db)
        # Side outputs collected across a single copilot run.
        self.citations: list[Citation] = []
        self.proposed_actions: list[ProposedAction] = []
        self.called: list[str] = []

    # OpenAI tool schemas ------------------------------------------------------
    def specs(self) -> list[dict[str, Any]]:
        customer_arg = {
            "customer_id": {
                "type": "string",
                "description": "UUID of the customer.",
            }
        }
        return [
            self._fn(
                "get_customer_billing_summary",
                "Get a customer's plan, outstanding balance, and latest invoice/payment.",
                {"type": "object", "properties": customer_arg, "required": ["customer_id"]},
            ),
            self._fn(
                "list_invoices",
                "List a customer's invoices (most recent first).",
                {
                    "type": "object",
                    "properties": {
                        **customer_arg,
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                    "required": ["customer_id"],
                },
            ),
            self._fn(
                "list_payments",
                "List a customer's payments (most recent first).",
                {
                    "type": "object",
                    "properties": {
                        **customer_arg,
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                    "required": ["customer_id"],
                },
            ),
            self._fn(
                "get_plan",
                "Get the plan a customer is on (name, price, interval).",
                {"type": "object", "properties": customer_arg, "required": ["customer_id"]},
            ),
            self._fn(
                "search_knowledge",
                "Search the knowledge base for policy/how-to content. Returns citations.",
                {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                    },
                    "required": ["query"],
                },
            ),
            self._fn(
                "propose_checkout_session",
                "Queue a Stripe checkout/subscription for HUMAN APPROVAL. Does not charge.",
                {
                    "type": "object",
                    "properties": {
                        **customer_arg,
                        "reason": {"type": "string"},
                    },
                    "required": ["customer_id", "reason"],
                },
            ),
            self._fn(
                "propose_refund",
                "Queue a refund/credit for HUMAN APPROVAL. Does not move money.",
                {
                    "type": "object",
                    "properties": {
                        **customer_arg,
                        "reason": {"type": "string"},
                    },
                    "required": ["customer_id", "reason"],
                },
            ),
        ]

    @staticmethod
    def _fn(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }

    # Execution ----------------------------------------------------------------
    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.called.append(name)
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            return handler(arguments)
        except Exception as exc:  # noqa: BLE001 - surface tool errors to the model
            return {"error": str(exc)}

    def _tool_get_customer_billing_summary(self, args: dict[str, Any]) -> dict[str, Any]:
        customer_id = _parse_uuid(args.get("customer_id"))
        if customer_id is None:
            return {"error": "A valid customer_id is required."}
        summary = self.billing.customer_summary(customer_id)
        return summary.model_dump(mode="json")

    def _tool_list_invoices(self, args: dict[str, Any]) -> dict[str, Any]:
        customer_id = _parse_uuid(args.get("customer_id"))
        if customer_id is None:
            return {"error": "A valid customer_id is required."}
        limit = int(args.get("limit", 10))
        invoices, total = self.billing.list_invoices(
            limit=limit, offset=0, customer_id=customer_id
        )
        return {
            "total": total,
            "invoices": [InvoiceRead.model_validate(i).model_dump(mode="json") for i in invoices],
        }

    def _tool_list_payments(self, args: dict[str, Any]) -> dict[str, Any]:
        customer_id = _parse_uuid(args.get("customer_id"))
        if customer_id is None:
            return {"error": "A valid customer_id is required."}
        limit = int(args.get("limit", 10))
        payments, total = self.billing.list_payments(
            limit=limit, offset=0, customer_id=customer_id
        )
        return {
            "total": total,
            "payments": [PaymentRead.model_validate(p).model_dump(mode="json") for p in payments],
        }

    def _tool_get_plan(self, args: dict[str, Any]) -> dict[str, Any]:
        customer_id = _parse_uuid(args.get("customer_id"))
        if customer_id is None:
            return {"error": "A valid customer_id is required."}
        customer = self.customers.get(customer_id)
        if customer is None:
            return {"error": f"Customer {customer_id} not found."}
        if customer.plan is None:
            return {"plan": None, "message": "Customer has no plan assigned."}
        plan = customer.plan
        return {
            "plan": {
                "name": plan.name,
                "price_amount": str(plan.price_amount),
                "currency": plan.currency,
                "interval": plan.interval.value,
            }
        }

    def _tool_search_knowledge(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "A non-empty query is required."}
        limit = int(args.get("limit", 5))
        results = self.knowledge.search(query, self.current_user, limit=limit)
        payload: list[dict[str, Any]] = []
        for result in results:
            snippet = result.snippet[:_SNIPPET_LEN]
            self.citations.append(
                Citation(
                    article_id=result.article_id,
                    chunk_id=result.chunk_id,
                    title=result.title,
                    snippet=snippet,
                )
            )
            payload.append(
                {
                    "article_id": str(result.article_id),
                    "title": result.title,
                    "snippet": snippet,
                }
            )
        return {"results": payload}

    def _tool_propose_checkout_session(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._propose("checkout_session", args)

    def _tool_propose_refund(self, args: dict[str, Any]) -> dict[str, Any]:
        return self._propose("refund", args)

    def _propose(self, action_type: str, args: dict[str, Any]) -> dict[str, Any]:
        customer_id = _parse_uuid(args.get("customer_id"))
        reason = str(args.get("reason", "")).strip()
        self.proposed_actions.append(
            ProposedAction(
                type=action_type,
                customer_id=customer_id,
                reason=reason,
                requires_approval=True,
            )
        )
        return {
            "status": "queued_for_approval",
            "action": action_type,
            "message": "This action is queued and requires a human agent to approve it.",
        }
