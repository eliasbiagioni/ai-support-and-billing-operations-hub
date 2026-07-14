"""Shared FastAPI dependencies: DB session, pagination, and a mocked current user.

Auth is intentionally mocked in Phase 0-1 (PRD 6.1). The `get_current_user`
dependency is the single seam that real JWT/session auth will replace later, so
routes and services already depend on an authenticated principal.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

# Stable id for the synthesized fallback admin when no user is seeded yet.
MOCK_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def get_pagination(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Return the mocked current user.

    Falls back to the first active user (the seeded admin). If no user exists yet
    (e.g. an empty test DB), synthesize a transient admin so endpoints stay usable.
    """

    user = db.scalars(
        select(User).where(User.active.is_(True)).order_by(User.created_at)
    ).first()
    if user is not None:
        return user
    return User(
        id=MOCK_USER_ID,
        name="Mock Admin",
        email="admin@supportledger.local",
        role=UserRole.admin,
        active=True,
    )
