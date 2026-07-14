"""Stripe webhook router (PRD 8.3). Verifies signatures and processes idempotently."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.integrations.stripe_client import StripeClient, get_stripe_client
from app.models.user import User
from app.repositories.billing_repository import BillingRepository
from app.schemas.billing import WebhookAck, WebhookEventRead
from app.schemas.common import Page
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", response_model=WebhookAck)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    db: Session = Depends(get_db),
    stripe: StripeClient = Depends(get_stripe_client),
) -> WebhookAck:
    payload = await request.body()
    processed = WebhookService(db, stripe).process(
        payload=payload, signature=stripe_signature
    )
    return WebhookAck(received=True, processed=processed)


@router.get("/events", response_model=Page[WebhookEventRead])
def list_webhook_events(
    pagination: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[WebhookEventRead]:
    items, total = BillingRepository(db).list_events(
        limit=pagination.limit, offset=pagination.offset
    )
    return Page[WebhookEventRead](
        items=[WebhookEventRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
