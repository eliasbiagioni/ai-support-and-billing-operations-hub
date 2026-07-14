"""User + authentication business logic (Phase 7).

No public self-registration: users are provisioned by admins. Authentication
verifies credentials and issues a JWT.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationAppError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def authenticate(self, email: str, password: str) -> tuple[User, str]:
        user = self.repo.get_by_email(email)
        if user is None or not user.password_hash:
            raise AuthenticationError("Invalid email or password.")
        if not user.active:
            raise AuthenticationError("This account is disabled.")
        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        token = create_access_token(subject=user.id, role=user.role.value)
        return user, token

    def list_users(self, *, limit: int, offset: int) -> tuple[list[User], int]:
        return self.repo.list(limit=limit, offset=offset)

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def create_user(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email) is not None:
            raise ConflictError(f"A user with email {payload.email} already exists.")
        user = User(
            name=payload.name,
            email=payload.email,
            role=payload.role,
            active=payload.active,
            password_hash=hash_password(payload.password),
        )
        self.repo.add(user)
        self.db.commit()
        return self.get_user(user.id)

    def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(user, field, value)
        self.db.commit()
        return self.get_user(user.id)

    def reset_password(self, user_id: uuid.UUID, new_password: str) -> User:
        user = self.get_user(user_id)
        user.password_hash = hash_password(new_password)
        self.db.commit()
        return user

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not user.password_hash or not verify_password(
            current_password, user.password_hash
        ):
            raise ValidationAppError("Current password is incorrect.")
        user.password_hash = hash_password(new_password)
        self.db.commit()
