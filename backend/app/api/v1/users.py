"""Admin-only user management API (Phase 7). No public signup."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_pagination, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import PasswordReset, UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserRead])
def list_users(
    pagination: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Page[UserRead]:
    items, total = UserService(db).list_users(
        limit=pagination.limit, offset=pagination.offset
    )
    return Page[UserRead](
        items=[UserRead.model_validate(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserRead:
    return UserRead.model_validate(UserService(db).create_user(payload))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserRead:
    return UserRead.model_validate(UserService(db).update_user(user_id, payload))


@router.post("/{user_id}/reset-password", response_model=UserRead)
def reset_password(
    user_id: uuid.UUID,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserRead:
    return UserRead.model_validate(
        UserService(db).reset_password(user_id, payload.new_password)
    )
