"""AI guardrails: PII redaction and prompt-injection detection (Phase 6).

Applied to user-supplied text before it reaches the LLM so sensitive data is
masked and obvious injection attempts are flagged. Returns risk flags that are
surfaced in API responses and recorded on ``AIAuditLog`` for review.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# 13-16 digit sequences allowing spaces/dashes (card-like).
_CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
# Loose phone matcher: 7-15 digits with optional separators/leading +.
_PHONE = re.compile(r"(?<![\w.])\+?\d(?:[\s\-.]?\d){6,14}(?![\w.])")

_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard the above",
    "disregard previous",
    "reveal your instructions",
    "reveal your system prompt",
    "you are now",
    "act as though",
)


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Mask emails, card-like numbers, and phone numbers. Returns (text, flags)."""

    flags: list[str] = []
    redacted = text

    redacted, n = _EMAIL.subn("[REDACTED_EMAIL]", redacted)
    if n:
        flags.append("pii_email_redacted")
    # Card before phone: card digit runs would otherwise be caught as phones.
    redacted, n = _CARD.subn("[REDACTED_CARD]", redacted)
    if n:
        flags.append("pii_card_redacted")
    redacted, n = _PHONE.subn("[REDACTED_PHONE]", redacted)
    if n:
        flags.append("pii_phone_redacted")

    return redacted, flags


def detect_injection(text: str) -> list[str]:
    lowered = text.lower()
    if any(marker in lowered for marker in _INJECTION_MARKERS):
        return ["prompt_injection"]
    return []


def apply_input_guardrails(text: str) -> tuple[str, list[str]]:
    """Sanitize input and return (sanitized_text, risk_flags)."""

    sanitized, flags = redact_pii(text)
    flags.extend(detect_injection(text))
    return sanitized, flags
