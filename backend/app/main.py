"""FastAPI application entrypoint (PRD 12.1)."""

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter

logger = get_logger("app.request")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "0",
}


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SupportLedger AI",
        version=__version__,
        description=(
            "AI Support & Billing Operations Hub - FastAPI backend. "
            "Support MVP, knowledge base, AI Assist, billing, RAG copilot, and auth."
        ),
        openapi_tags=[
            {"name": "health", "description": "Service health checks."},
            {"name": "auth", "description": "Authentication (login, current user)."},
            {"name": "users", "description": "Admin-only user management."},
            {"name": "customers", "description": "Customer management."},
            {"name": "tickets", "description": "Support ticket workflows."},
            {"name": "dashboard", "description": "Operational summary metrics."},
            {"name": "knowledge", "description": "Knowledge base articles and search."},
            {"name": "ai", "description": "AI Assist + RAG billing copilot."},
            {"name": "billing", "description": "Stripe billing: invoices, payments, checkout."},
            {"name": "webhooks", "description": "Provider webhooks (Stripe)."},
        ],
    )

    # Rate limiting (enabled in production; see core.rate_limit).
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def _observability(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_id=%s %s %s failed after %.1fms",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s %s %s -> %d (%.1fms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
