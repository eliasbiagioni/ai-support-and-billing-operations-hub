"""Data access for knowledge base articles and chunks (PRD 12: repositories)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import ArticleVisibility
from app.models.knowledge_article import KnowledgeArticle
from app.models.knowledge_chunk import KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, article_id: uuid.UUID) -> KnowledgeArticle | None:
        stmt = (
            select(KnowledgeArticle)
            .where(KnowledgeArticle.id == article_id)
            .options(selectinload(KnowledgeArticle.chunks))
        )
        return self.db.scalars(stmt).first()

    def list(
        self,
        *,
        limit: int,
        offset: int,
        tag: str | None = None,
        active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[KnowledgeArticle], int]:
        filters = []
        if tag:
            filters.append(KnowledgeArticle.tags.ilike(f"%{tag}%"))
        if active is not None:
            filters.append(KnowledgeArticle.active.is_(active))
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    KnowledgeArticle.title.ilike(pattern),
                    KnowledgeArticle.content.ilike(pattern),
                    KnowledgeArticle.tags.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(KnowledgeArticle)
        list_stmt = (
            select(KnowledgeArticle)
            .options(selectinload(KnowledgeArticle.chunks))
            .order_by(KnowledgeArticle.title)
        )
        for condition in filters:
            count_stmt = count_stmt.where(condition)
            list_stmt = list_stmt.where(condition)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(list_stmt.limit(limit).offset(offset)).all())
        return items, total

    def add(self, article: KnowledgeArticle) -> KnowledgeArticle:
        self.db.add(article)
        self.db.flush()
        return article

    def delete_chunks(self, article_id: uuid.UUID) -> None:
        for chunk in self.db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.article_id == article_id)
        ).all():
            self.db.delete(chunk)
        self.db.flush()

    def add_chunk(self, chunk: KnowledgeChunk) -> KnowledgeChunk:
        self.db.add(chunk)
        self.db.flush()
        return chunk

    def search_chunks(
        self,
        query: str,
        *,
        visibilities: tuple[ArticleVisibility, ...],
        limit: int,
    ) -> list[tuple[KnowledgeArticle, KnowledgeChunk]]:
        pattern = f"%{query}%"
        stmt = (
            select(KnowledgeArticle, KnowledgeChunk)
            .join(KnowledgeChunk, KnowledgeChunk.article_id == KnowledgeArticle.id)
            .where(
                KnowledgeArticle.active.is_(True),
                KnowledgeArticle.visibility.in_(visibilities),
                or_(
                    KnowledgeChunk.content.ilike(pattern),
                    KnowledgeArticle.title.ilike(pattern),
                    KnowledgeArticle.tags.ilike(pattern),
                ),
            )
            .order_by(KnowledgeArticle.title, KnowledgeChunk.chunk_index)
            .limit(limit)
        )
        return [(article, chunk) for article, chunk in self.db.execute(stmt).all()]
