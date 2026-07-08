"""Seed demo data for local development and the portfolio demo (PRD 14.3).

Idempotent: if customers already exist the seed is skipped. Run with:
    python -m app.commands.seed
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal, engine
from app.models import Base, Customer, Plan, Ticket, TicketMessage, User
from app.models.enums import (
    BillingInterval,
    CustomerStatus,
    MessageAuthorType,
    MessageVisibility,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UserRole,
)

logger = get_logger(__name__)


def _seed_users(db: Session) -> list[User]:
    users = [
        User(name="Ava Admin", email="ava.admin@supportledger.local", role=UserRole.admin),
        User(name="Sam Support", email="sam.support@supportledger.local", role=UserRole.support_agent),
        User(name="Bianca Billing", email="bianca.billing@supportledger.local", role=UserRole.billing_agent),
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
        db.commit()
        logger.info(
            "Seed complete: %d users, %d plans, %d customers, %d tickets.",
            len(agents),
            len(plans),
            len(customers),
            len(_TICKET_BLUEPRINTS),
        )


if __name__ == "__main__":
    seed()
