"""SQLAlchemy declarative base and the shared model mixin."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class BaseModelMixin:
    """Shared columns for every model: a UUID primary key and timestamps.

    ``Uuid`` is cross-dialect: it maps to native ``UUID`` on PostgreSQL and to
    ``CHAR(32)`` on SQLite (used in tests). UUIDs are generated application-side
    via ``uuid4`` so inserts do not depend on a database default.
    """

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
