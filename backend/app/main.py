"""FastAPI application entrypoint (PRD 12.1)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SupportLedger AI",
        version=__version__,
        description=(
            "AI Support & Billing Operations Hub - FastAPI backend. "
            "Phases 0-4: support MVP, knowledge base, AI Assist, and Stripe billing."
        ),
        openapi_tags=[
            {"name": "health", "description": "Service health checks."},
            {"name": "customers", "description": "Customer management."},
            {"name": "tickets", "description": "Support ticket workflows."},
            {"name": "dashboard", "description": "Operational summary metrics."},
            {"name": "knowledge", "description": "Knowledge base articles and search."},
            {"name": "ai", "description": "AI Assist: classify, summarize, suggest replies."},
            {"name": "billing", "description": "Stripe billing: invoices, payments, checkout."},
            {"name": "webhooks", "description": "Provider webhooks (Stripe)."},
        ],
    )

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
