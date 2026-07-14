"""Seed demo data for local development and the portfolio demo (PRD 14.3).

Idempotent: if customers already exist the seed is skipped. Run with:
    python -m app.commands.seed
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models import (
    Base,
    Customer,
    Invoice,
    KnowledgeArticle,
    KnowledgeChunk,
    Payment,
    Plan,
    Ticket,
    TicketMessage,
    User,
)
from app.models.enums import (
    ArticleVisibility,
    BillingInterval,
    CustomerStatus,
    InvoiceStatus,
    MessageAuthorType,
    MessageVisibility,
    PaymentStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UserRole,
)
from app.services.knowledge_service import _split_content

logger = get_logger(__name__)


# Shared demo password for all seeded accounts (local/portfolio use only).
DEMO_PASSWORD = "password123"


def _seed_users(db: Session) -> list[User]:
    password_hash = hash_password(DEMO_PASSWORD)
    users = [
        User(name="Ava Admin", email="ava.admin@supportledger.io", role=UserRole.admin, password_hash=password_hash),
        User(name="Sam Support", email="sam.support@supportledger.io", role=UserRole.support_agent, password_hash=password_hash),
        User(name="Bianca Billing", email="bianca.billing@supportledger.io", role=UserRole.billing_agent, password_hash=password_hash),
    ]
    db.add_all(users)
    db.flush()
    return users


def _seed_plans(db: Session) -> dict[str, Plan]:
    plans = {
        "starter": Plan(
            name="Starter",
            price_amount=Decimal("29.00"),
            currency="usd",
            interval=BillingInterval.month,
            max_seats=5,
        ),
        "pro": Plan(
            name="Pro",
            price_amount=Decimal("99.00"),
            currency="usd",
            interval=BillingInterval.month,
            max_seats=25,
        ),
        "enterprise": Plan(
            name="Enterprise",
            price_amount=Decimal("499.00"),
            currency="usd",
            interval=BillingInterval.month,
            max_seats=None,
        ),
    }
    db.add_all(plans.values())
    db.flush()
    return plans


def _seed_customers(db: Session, plans: dict[str, Plan]) -> list[Customer]:
    customers = [
        Customer(
            company_name="Northwind Traders",
            contact_name="Grace Hopper",
            email="grace@northwind.example",
            status=CustomerStatus.active,
            plan_id=plans["pro"].id,
            notes="Long-time customer, expanding seats next quarter.",
        ),
        Customer(
            company_name="Contoso Ltd",
            contact_name="Alan Turing",
            email="alan@contoso.example",
            status=CustomerStatus.suspended,
            plan_id=plans["starter"].id,
            notes="Account suspended after a failed payment.",
        ),
        Customer(
            company_name="Fabrikam Inc",
            contact_name="Ada Lovelace",
            email="ada@fabrikam.example",
            status=CustomerStatus.overdue,
            plan_id=plans["pro"].id,
            notes="Invoice overdue by 14 days.",
        ),
        Customer(
            company_name="Adventure Works",
            contact_name="Katherine Johnson",
            email="katherine@adventureworks.example",
            status=CustomerStatus.trial,
            plan_id=plans["starter"].id,
            notes="On a 14-day trial, evaluating the Pro plan.",
        ),
        Customer(
            company_name="Globex Corporation",
            contact_name="Hedy Lamarr",
            email="hedy@globex.example",
            status=CustomerStatus.enterprise,
            plan_id=plans["enterprise"].id,
            notes="Enterprise agreement with a dedicated CSM.",
        ),
    ]
    db.add_all(customers)
    db.flush()
    return customers


_TICKET_BLUEPRINTS = [
    ("I paid yesterday but my account is still suspended", TicketCategory.billing, TicketPriority.urgent, TicketStatus.open),
    ("Duplicate charge on my last invoice", TicketCategory.billing, TicketPriority.high, TicketStatus.pending_billing),
    ("Where can I download my invoices?", TicketCategory.billing, TicketPriority.low, TicketStatus.new),
    ("Refund request for accidental upgrade", TicketCategory.billing, TicketPriority.high, TicketStatus.open),
    ("Payment keeps failing with my card", TicketCategory.billing, TicketPriority.high, TicketStatus.pending_customer),
    ("App crashes when exporting reports", TicketCategory.technical, TicketPriority.high, TicketStatus.open),
    ("API returns 500 on bulk import", TicketCategory.technical, TicketPriority.urgent, TicketStatus.open),
    ("Slow dashboard loading times", TicketCategory.technical, TicketPriority.medium, TicketStatus.new),
    ("Webhook events are delayed", TicketCategory.technical, TicketPriority.medium, TicketStatus.pending_billing),
    ("Cannot reset my password", TicketCategory.account, TicketPriority.medium, TicketStatus.open),
    ("Need to add a new team member", TicketCategory.account, TicketPriority.low, TicketStatus.new),
    ("Change account owner email", TicketCategory.account, TicketPriority.low, TicketStatus.resolved),
    ("How do I enable SSO?", TicketCategory.account, TicketPriority.medium, TicketStatus.new),
    ("Feature request: dark mode", TicketCategory.product, TicketPriority.low, TicketStatus.new),
    ("Is there a mobile app?", TicketCategory.product, TicketPriority.low, TicketStatus.closed),
    ("Bulk edit for tickets would help", TicketCategory.product, TicketPriority.low, TicketStatus.new),
    ("General question about data retention", TicketCategory.other, TicketPriority.low, TicketStatus.new),
    ("Angry: still no response after 3 days!", TicketCategory.other, TicketPriority.urgent, TicketStatus.open),
    ("Onboarding help for new workspace", TicketCategory.other, TicketPriority.medium, TicketStatus.pending_customer),
    ("Plan limits unclear on pricing page", TicketCategory.billing, TicketPriority.medium, TicketStatus.new),
]


def _seed_tickets(db: Session, customers: list[Customer], agents: list[User]) -> None:
    support_agent = next((u for u in agents if u.role == UserRole.support_agent), agents[0])
    for index, (subject, category, priority, status) in enumerate(_TICKET_BLUEPRINTS):
        customer = customers[index % len(customers)]
        ticket = Ticket(
            customer_id=customer.id,
            subject=subject,
            description=(
                f"{subject}. Reported by {customer.contact_name} at {customer.company_name}. "
                "This is seeded demo content for portfolio purposes."
            ),
            source="web",
            status=status,
            priority=priority,
            category=category,
            assigned_to=support_agent.id if index % 3 else None,
        )
        db.add(ticket)
        db.flush()

        db.add(
            TicketMessage(
                ticket_id=ticket.id,
                author_type=MessageAuthorType.customer,
                body=f"{subject}. Please help as soon as possible.",
                visibility=MessageVisibility.public,
            )
        )
        if index % 2 == 0:
            db.add(
                TicketMessage(
                    ticket_id=ticket.id,
                    author_type=MessageAuthorType.agent,
                    author_id=support_agent.id,
                    body="Thanks for reaching out - I'm looking into this now.",
                    visibility=MessageVisibility.internal,
                )
            )


_ARTICLE_BLUEPRINTS: list[tuple[str, str, str, ArticleVisibility]] = [
    (
        "Refund policy",
        "We offer prorated refunds within 14 days of a charge.\n\n"
        "Refunds are issued to the original payment method and take 5-10 business "
        "days to appear. Annual plans cancelled mid-term are refunded for the unused "
        "months. Contact billing to start a refund.",
        "refund,billing,policy",
        ArticleVisibility.public,
    ),
    (
        "Fixing a failed payment",
        "A payment can fail due to an expired card, insufficient funds, or a bank "
        "block.\n\nAsk the customer to update their card in the billing portal, then "
        "retry the invoice. If it still fails, the bank must authorize the charge. "
        "Accounts are suspended after three consecutive failures.",
        "billing,payment,dunning",
        ArticleVisibility.internal,
    ),
    (
        "Cancelling a subscription",
        "Customers can cancel any time from Settings > Billing.\n\n"
        "Cancellation stops future renewals; access continues until the end of the "
        "current period. Reactivation restores the previous plan. Enterprise "
        "contracts require written notice per the agreement.",
        "cancellation,billing,subscription",
        ArticleVisibility.public,
    ),
    (
        "Invoice FAQ",
        "Invoices are generated at the start of each billing cycle.\n\n"
        "They can be downloaded as PDF from the billing portal. VAT/tax IDs can be "
        "added before the next cycle. Historical invoices remain available for seven "
        "years for compliance.",
        "invoice,billing,faq",
        ArticleVisibility.public,
    ),
    (
        "Security and data handling",
        "Data is encrypted in transit (TLS) and at rest (AES-256).\n\n"
        "We follow least-privilege access and log administrative actions. Report "
        "suspected incidents to security immediately. Customer data is never used to "
        "train third-party models.",
        "security,compliance,data",
        ArticleVisibility.internal,
    ),
    (
        "Understanding plan limits",
        "Each plan includes a set number of seats and monthly action quota.\n\n"
        "Starter includes 5 seats, Pro includes 25, and Enterprise is custom. "
        "Overages prompt an upgrade suggestion rather than a hard block. Limits reset "
        "on the billing anniversary.",
        "plans,limits,billing",
        ArticleVisibility.public,
    ),
    (
        "Onboarding a new workspace",
        "New workspaces start with a guided setup checklist.\n\n"
        "Invite teammates, connect your data sources, and configure ticket routing. "
        "The onboarding wizard can be re-run from Settings. Most teams are fully set "
        "up within a day.",
        "onboarding,account,setup",
        ArticleVisibility.internal,
    ),
    (
        "Support SLA targets",
        "First response targets: urgent 1 hour, high 4 hours, medium 1 business day.\n\n"
        "Resolution times vary by complexity. SLAs apply during business hours unless "
        "an enterprise 24/7 add-on is active. Breaches are escalated to a team lead.",
        "sla,support,policy",
        ArticleVisibility.internal,
    ),
]


def _seed_knowledge(db: Session, author: User) -> int:
    for title, content, tags, visibility in _ARTICLE_BLUEPRINTS:
        article = KnowledgeArticle(
            title=title,
            content=content,
            tags=tags,
            visibility=visibility,
            active=True,
            created_by=author.id,
        )
        db.add(article)
        db.flush()
        for index, text in enumerate(_split_content(content)):
            db.add(
                KnowledgeChunk(
                    article_id=article.id,
                    chunk_index=index,
                    content=text,
                    token_count=max(1, len(text) // 4),
                )
            )
    return len(_ARTICLE_BLUEPRINTS)


def _seed_billing(db: Session, customers: list[Customer]) -> tuple[int, int]:
    invoices = 0
    payments = 0
    # A paid invoice with a successful payment.
    northwind = customers[0]
    paid_invoice = Invoice(
        customer_id=northwind.id,
        amount_due=Decimal("99.00"),
        amount_paid=Decimal("99.00"),
        currency="usd",
        status=InvoiceStatus.paid,
        description="Pro plan - monthly",
    )
    db.add(paid_invoice)
    db.flush()
    db.add(
        Payment(
            customer_id=northwind.id,
            invoice_id=paid_invoice.id,
            amount=Decimal("99.00"),
            currency="usd",
            status=PaymentStatus.succeeded,
        )
    )
    invoices += 1
    payments += 1

    # An open (unpaid) invoice for an overdue customer.
    fabrikam = customers[2]
    db.add(
        Invoice(
            customer_id=fabrikam.id,
            amount_due=Decimal("99.00"),
            amount_paid=Decimal("0.00"),
            currency="usd",
            status=InvoiceStatus.open,
            description="Pro plan - monthly (overdue)",
        )
    )
    invoices += 1

    # A failed payment for a suspended customer.
    contoso = customers[1]
    db.add(
        Payment(
            customer_id=contoso.id,
            amount=Decimal("29.00"),
            currency="usd",
            status=PaymentStatus.failed,
            failure_reason="Your card was declined.",
        )
    )
    payments += 1
    return invoices, payments


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = db.scalar(select(Customer.id).limit(1))
        if existing is not None:
            logger.info("Seed skipped: data already present.")
            return

        agents = _seed_users(db)
        plans = _seed_plans(db)
        customers = _seed_customers(db, plans)
        _seed_tickets(db, customers, agents)
        article_count = _seed_knowledge(db, agents[0])
        invoice_count, payment_count = _seed_billing(db, customers)
        db.commit()
        logger.info(
            "Seed complete: %d users, %d plans, %d customers, %d tickets, "
            "%d articles, %d invoices, %d payments.",
            len(agents),
            len(plans),
            len(customers),
            len(_TICKET_BLUEPRINTS),
            article_count,
            invoice_count,
            payment_count,
        )


if __name__ == "__main__":
    seed()
