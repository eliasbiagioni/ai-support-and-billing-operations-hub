"""Knowledge base API router (PRD 10)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.knowledge_article import KnowledgeArticle
from app.models.user import User
from app.schemas.common import Page
from app.schemas.knowledge import (
    ArticleCreate,
    ArticleRead,
    ArticleUpdate,
    SearchResult,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _to_read(article: KnowledgeArticle) -> ArticleRead:
    read = ArticleRead.model_validate(article)
    return read.model_copy(update={"chunk_count": len(article.chunks)})


@router.get("/articles", response_model=Page[ArticleRead])
def list_articles(
    pagination: Pagination = Depends(get_pagination),
    tag: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Search title/content/tags"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[ArticleRead]:
    items, total = KnowledgeService(db).list_articles(
        limit=pagination.limit,
        offset=pagination.offset,
        tag=tag,
        active=active,
        search=q,
    )
    return Page[ArticleRead](
        items=[_to_read(item) for item in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/articles", response_model=ArticleRead, status_code=status.HTTP_201_CREATED
)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArticleRead:
    article = KnowledgeService(db).create_article(payload, current_user)
    return _to_read(article)


@router.get("/search", response_model=list[SearchResult])
def search_articles(
    q: str = Query(min_length=1, description="Keyword search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SearchResult]:
    return KnowledgeService(db).search(q, current_user)


@router.get("/articles/{article_id}", response_model=ArticleRead)
def get_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ArticleRead:
    article = KnowledgeService(db).get_article(article_id)
    return _to_read(article)


@router.patch("/articles/{article_id}", response_model=ArticleRead)
def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ArticleRead:
    article = KnowledgeService(db).update_article(article_id, payload)
    return _to_read(article)


@router.post("/articles/{article_id}/chunk", response_model=ArticleRead)
def chunk_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ArticleRead:
    article = KnowledgeService(db).chunk_article(article_id)
    return _to_read(article)
