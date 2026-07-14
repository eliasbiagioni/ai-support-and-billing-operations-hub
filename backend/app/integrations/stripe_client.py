"""Stripe client abstraction (PRD 8).

Real-only integration: ``StripeClient`` wraps the Stripe SDK and requires
``STRIPE_SECRET_KEY``. Tests override the ``get_stripe_client`` dependency with a
fake so no network calls or real signatures are needed in CI.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.core.config import settings
from app.core.errors import AppError


class StripeConfigError(AppError):
    status_code = 503
    code = "stripe_unavailable"


class StripeError(AppError):
    status_code = 502
    code = "stripe_error"


class StripeClient(Protocol):
    def create_checkout_session(
        self,
        *,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None,
        metadata: dict[str, str],
    ) -> dict[str, Any]:
        """Create a Checkout Session and return at least {id, url}."""
        ...

    def construct_event(self, *, payload: bytes, signature: str) -> dict[str, Any]:
        """Verify the webhook signature and return the parsed event dict."""
        ...


class RealStripeClient:
    def __init__(self, *, secret_key: str, webhook_secret: str) -> None:
        if not secret_key:
            raise StripeConfigError(
                "Stripe secret key is not configured. Set STRIPE_SECRET_KEY to use billing."
            )
        import stripe

        self._stripe = stripe
        self._stripe.api_key = secret_key
        self._webhook_secret = webhook_secret

    def create_checkout_session(
        self,
        *,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None,
        metadata: dict[str, str],
    ) -> dict[str, Any]:
        try:
            session = self._stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata=metadata,
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise StripeError(f"Failed to create checkout session: {exc}") from exc
        return {"id": session["id"], "url": session["url"]}

    def construct_event(self, *, payload: bytes, signature: str) -> dict[str, Any]:
        if not self._webhook_secret:
            raise StripeConfigError("Stripe webhook secret is not configured.")
        try:
            event = self._stripe.Webhook.construct_event(
                payload, signature, self._webhook_secret
            )
        except Exception as exc:  # noqa: BLE001 - includes signature failures
            raise StripeError(f"Invalid webhook signature: {exc}") from exc
        return event._to_dict_recursive()


def get_stripe_client() -> StripeClient:
    return RealStripeClient(
        secret_key=settings.STRIPE_SECRET_KEY,
        webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
    )
