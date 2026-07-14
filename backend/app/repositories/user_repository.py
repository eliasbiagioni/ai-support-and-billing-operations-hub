"""Data access for users (PRD 12: repositories layer)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalars(
            select(User).where(func.lower(User.email) == email.lower())
        ).first()

    def list(self, *, limit: int, offset: int) -> tuple[list[User], int]:
        total = self.db.scalar(select(func.count()).select_from(User)) or 0
        items = list(
            self.db.scalars(
                select(User).order_by(User.name).limit(limit).offset(offset)
            ).all()
        )
        return items, total

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
