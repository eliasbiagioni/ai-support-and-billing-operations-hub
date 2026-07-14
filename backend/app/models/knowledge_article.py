"""Knowledge base article model (PRD 7.4)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BaseModelMixin
from app.models.enums import ArticleVisibility

if TYPE_CHECKING:
    from app.models.knowledge_chunk import KnowledgeChunk


class KnowledgeArticle(BaseModelMixin, Base):
    __tablename__ = "knowledge_articles"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Comma-separated tags stored as text; kept simple for keyword search (PRD 7.4).
    tags: Mapped[str] = mapped_column(Text, default="", nullable=False)
    visibility: Mapped[ArticleVisibility] = mapped_column(
        Enum(ArticleVisibility, name="article_visibility"),
        default=ArticleVisibility.internal,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    chunks: Mapped[list[KnowledgeChunk]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index",
    )
