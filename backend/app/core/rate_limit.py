"""Shared rate limiter (Phase 7 hardening).

Uses slowapi keyed on client IP. Enabled only in production so local dev and the
test suite are not throttled. Applied to auth + AI endpoints via decorators.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.is_production)
