"""Shared FastAPI dependencies: DB session, pagination, auth, and RBAC.

Phase 7 replaces the earlier mocked principal with real JWT auth. Every
authenticated route depends on ``get_current_user``; role-restricted routes add
``require_roles(...)``.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, AuthorizationError
from app.core.security import JWTError, decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def get_pagination(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Not authenticated.")
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    subject = payload.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except (ValueError, TypeError) as exc:
        raise AuthenticationError("Invalid token subject.") from exc

    user = db.get(User, user_id)
    if user is None or not user.active:
        raise AuthenticationError("User no longer exists or is disabled.")
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the current user has one of ``roles``."""

    allowed = set(roles)

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise AuthorizationError(
                "You do not have permission to perform this action."
            )
        return current_user

    return _dependency


require_admin = require_roles(UserRole.admin)
