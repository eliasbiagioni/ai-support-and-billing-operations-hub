"""ORM models. Importing this package registers all tables on the shared Base."""

from app.db.base import Base
from app.models.ai_audit_log import AIAuditLog
from app.models.conversation import Conversation, ConversationMessage
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.knowledge_article import KnowledgeArticle
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.ticket import Ticket, TicketMessage
from app.models.user import User
from app.models.webhook_event import WebhookEvent

__all__ = [
    "AIAuditLog",
    "Base",
    "Conversation",
    "ConversationMessage",
    "Customer",
    "Invoice",
    "KnowledgeArticle",
    "KnowledgeChunk",
    "Payment",
    "Plan",
    "Ticket",
    "TicketMessage",
    "User",
    "WebhookEvent",
]
