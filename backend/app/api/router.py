"""Aggregate API router that includes all domain routers under /api."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    auth,
    billing,
    customers,
    dashboard,
    health,
    knowledge,
    tickets,
    users,
    webhooks,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(tickets.router)
api_router.include_router(dashboard.router)
api_router.include_router(knowledge.router)
api_router.include_router(ai.router)
api_router.include_router(billing.router)
api_router.include_router(webhooks.router)
