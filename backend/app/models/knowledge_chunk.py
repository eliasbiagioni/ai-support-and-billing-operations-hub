"""Knowledge base chunk model - prepares KB content for future RAG (PRD 7.4)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, BaseModelMixin

if TYPE_CHECKING:
    from app.models.knowledge_article import KnowledgeArticle


class KnowledgeChunk(BaseModelMixin, Base):
    __tablename__ = "knowledge_chunks"

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Placeholder for a future vector store reference (embedding id / external key).
    embedding_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # pgvector column on Postgres; JSON list on SQLite (tests) via with_variant so
    # the same Python value (list[float]) works across dialects (Phase 6 RAG).
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIM).with_variant(JSON, "sqlite"),
        nullable=True,
    )
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    article: Mapped[KnowledgeArticle] = relationship(back_populates="chunks")
