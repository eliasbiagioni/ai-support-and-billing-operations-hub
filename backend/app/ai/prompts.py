"""Prompt templates for AI Assist (PRD Appendix A).

Kept as plain functions so they are easy to test and version. Each returns a
(system, user) pair. Classification asks for strict JSON so the output can be
validated against ``TicketClassification``.
"""

from __future__ import annotations

CLASSIFY_SYSTEM = (
    "You are a support triage assistant for a B2B SaaS help desk. "
    "Classify the ticket and respond ONLY with a JSON object using exactly these "
    "keys: category (one of billing, technical, account, product, other), "
    "urgency (one of low, medium, high, urgent), "
    "sentiment (one of positive, neutral, negative), "
    "billing_lookup_required (boolean), "
    "suggested_team (short string), "
    "reasoning_summary (one short sentence). Do not include any other text."
)

SUMMARY_SYSTEM = (
    "You are a support assistant. Summarize the ticket and its conversation into "
    "3-5 concise bullet points an agent can skim. Focus on the customer's problem, "
    "what has been tried, and the current state. Plain text only."
)

SUGGEST_REPLY_SYSTEM = (
    "You are a helpful, empathetic support agent. Draft a reply to the customer's "
    "latest message. Be concise, professional, and actionable. Do not invent "
    "account details or make promises about refunds/credits; suggest next steps "
    "instead. This is a draft for a human agent to review before sending."
)


def _ticket_block(subject: str, description: str, messages: list[str]) -> str:
    lines = [f"Subject: {subject}", f"Description: {description}"]
    if messages:
        lines.append("Conversation:")
        lines.extend(f"- {m}" for m in messages)
    return "\n".join(lines)


def classify_prompt(subject: str, description: str) -> tuple[str, str]:
    user = _ticket_block(subject, description, [])
    return CLASSIFY_SYSTEM, user


def summary_prompt(
    subject: str, description: str, messages: list[str]
) -> tuple[str, str]:
    return SUMMARY_SYSTEM, _ticket_block(subject, description, messages)


def suggest_reply_prompt(
    subject: str, description: str, messages: list[str]
) -> tuple[str, str]:
    return SUGGEST_REPLY_SYSTEM, _ticket_block(subject, description, messages)


COPILOT_SYSTEM = (
    "You are the SupportLedger Billing Copilot, assisting a human support/billing "
    "agent. Answer questions about customers, invoices, payments, plans, and policy "
    "using ONLY the provided tools for facts - never invent account data. "
    "Call tools to look up billing summaries, invoices, payments, plans, and to "
    "search the knowledge base. When you reference a knowledge base article, keep "
    "the answer grounded in what the tools return. "
    "You cannot perform write actions or move money directly: for anything risky "
    "(starting a checkout/subscription, issuing a refund or credit) you MUST call "
    "the matching 'propose_*' tool to queue it for human approval, then tell the "
    "agent it is awaiting their confirmation. Be concise and professional."
)


def copilot_context(customer_id: str | None, ticket_id: str | None) -> str | None:
    """Optional context line pinning the conversation to a customer/ticket."""

    parts: list[str] = []
    if customer_id:
        parts.append(f"Active customer_id: {customer_id}")
    if ticket_id:
        parts.append(f"Active ticket_id: {ticket_id}")
    return "\n".join(parts) if parts else None


RAG_CONTEXT_HEADER = (
    "Relevant knowledge base excerpts (cite these; do not contradict them):"
)


def rag_augmented_reply_prompt(
    subject: str, description: str, messages: list[str], contexts: list[str]
) -> tuple[str, str]:
    """Suggest-reply prompt grounded in retrieved KB excerpts (Phase 6 RAG)."""

    user = _ticket_block(subject, description, messages)
    if contexts:
        joined = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
        user = f"{user}\n\n{RAG_CONTEXT_HEADER}\n{joined}"
    return SUGGEST_REPLY_SYSTEM, user
