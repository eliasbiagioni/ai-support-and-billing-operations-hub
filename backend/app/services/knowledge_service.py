"""Business rules for the knowledge base: CRUD, chunking, and search (PRD 7.4)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.enums import ArticleVisibility
from app.models.knowledge_article import KnowledgeArticle
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.user import User
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import ArticleCreate, ArticleUpdate, SearchResult

# Approximate characters per chunk. A deliberately simple splitter that keeps
# paragraphs together where possible; real embeddings/tokenization arrive with RAG.
_CHUNK_SIZE = 500
_SNIPPET_LEN = 240


def _tags_to_str(tags: list[str]) -> str:
    return ",".join(tag.strip() for tag in tags if tag.strip())


def _split_content(content: str, size: int = _CHUNK_SIZE) -> list[str]:
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if not buffer:
            buffer = paragraph
        elif len(buffer) + len(paragraph) + 2 <= size:
            buffer = f"{buffer}\n\n{paragraph}"
        else:
            chunks.append(buffer)
            buffer = paragraph
        # Hard-split very long single paragraphs.
        while len(buffer) > size:
            chunks.append(buffer[:size])
            buffer = buffer[size:]
    if buffer:
        chunks.append(buffer)
    return chunks or ([content] if content else [])


class KnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = KnowledgeRepository(db)

    def list_articles(
        self,
        *,
        limit: int,
        offset: int,
        tag: str | None = None,
        active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[KnowledgeArticle], int]:
        return self.repo.list(
            limit=limit, offset=offset, tag=tag, active=active, search=search
        )

    def get_article(self, article_id: uuid.UUID) -> KnowledgeArticle:
        article = self.repo.get(article_id)
        if article is None:
            raise NotFoundError(f"Article {article_id} not found")
        return article

    def create_article(
        self, payload: ArticleCreate, current_user: User
    ) -> KnowledgeArticle:
        article = KnowledgeArticle(
            title=payload.title,
            content=payload.content,
            tags=_tags_to_str(payload.tags),
            visibility=payload.visibility,
            active=payload.active,
            created_by=current_user.id,
        )
        self.repo.add(article)
        self.db.flush()
        self._rebuild_chunks(article)
        self.db.commit()
        return self.get_article(article.id)

    def update_article(
        self, article_id: uuid.UUID, payload: ArticleUpdate
    ) -> KnowledgeArticle:
        article = self.get_article(article_id)
        data = payload.model_dump(exclude_unset=True)
        content_changed = False
        for field, value in data.items():
            if field == "tags":
                article.tags = _tags_to_str(value or [])
            else:
                if field == "content":
                    content_changed = True
                setattr(article, field, value)
        if content_changed:
            self._rebuild_chunks(article)
        self.db.commit()
        return self.get_article(article.id)

    def chunk_article(self, article_id: uuid.UUID) -> KnowledgeArticle:
        article = self.get_article(article_id)
        self._rebuild_chunks(article)
        self.db.commit()
        return self.get_article(article.id)

    def _rebuild_chunks(self, article: KnowledgeArticle) -> None:
        self.repo.delete_chunks(article.id)
        for index, text in enumerate(_split_content(article.content)):
            self.repo.add_chunk(
                KnowledgeChunk(
                    article_id=article.id,
                    chunk_index=index,
                    content=text,
                    token_count=max(1, len(text) // 4),
                )
            )

    def search(
        self, query: str, current_user: User, *, limit: int = 20
    ) -> list[SearchResult]:
        visibilities = self._visible_scopes(current_user)
        hits = self.repo.search_chunks(query, visibilities=visibilities, limit=limit)
        results: list[SearchResult] = []
        for article, chunk in hits:
            results.append(
                SearchResult(
                    article_id=article.id,
                    title=article.title,
                    visibility=article.visibility,
                    chunk_id=chunk.id,
                    snippet=chunk.content[:_SNIPPET_LEN],
                )
            )
        return results

    @staticmethod
    def _visible_scopes(current_user: User) -> tuple[ArticleVisibility, ...]:
        # Every authenticated agent sees internal + public articles here; the
        # visibility split is what public-facing surfaces would filter on later.
        return (ArticleVisibility.internal, ArticleVisibility.public)
