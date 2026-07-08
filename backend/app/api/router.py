"""Aggregate API router that includes all domain routers under /api."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import customers, dashboard, health, tickets

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(customers.router)
api_router.include_router(tickets.router)
api_router.include_router(dashboard.router)
