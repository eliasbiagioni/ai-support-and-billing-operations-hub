"""Constrained value enums shared across models and schemas (PRD 9.1)."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    support_agent = "support_agent"
    billing_agent = "billing_agent"
    viewer = "viewer"


class CustomerStatus(StrEnum):
    active = "active"
    suspended = "suspended"
    overdue = "overdue"
    trial = "trial"
    enterprise = "enterprise"


class TicketStatus(StrEnum):
    new = "new"
    open = "open"
    pending_customer = "pending_customer"
    pending_billing = "pending_billing"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketCategory(StrEnum):
    billing = "billing"
    technical = "technical"
    account = "account"
    product = "product"
    other = "other"


class MessageAuthorType(StrEnum):
    agent = "agent"
    customer = "customer"
    ai = "ai"
    system = "system"


class MessageVisibility(StrEnum):
    internal = "internal"
    public = "public"


class BillingInterval(StrEnum):
    month = "month"
    year = "year"


class ArticleVisibility(StrEnum):
    internal = "internal"
    public = "public"


class InvoiceStatus(StrEnum):
    draft = "draft"
    open = "open"
    paid = "paid"
    void = "void"
    uncollectible = "uncollectible"


class PaymentStatus(StrEnum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"
