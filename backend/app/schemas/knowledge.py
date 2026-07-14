"""Pydantic schemas for the knowledge base (PRD 7.4)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ArticleVisibility


def _normalize_tags(value: object) -> list[str]:
    """Accept either a list or a comma-separated string of tags."""

    if value is None:
        return []
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(",") if tag.strip()]
    if isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return []


class ArticleBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    visibility: ArticleVisibility = ArticleVisibility.internal
    active: bool = True

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: object) -> list[str]:
        return _normalize_tags(value)


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    visibility: ArticleVisibility | None = None
    active: bool | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: object) -> list[str] | None:
        if value is None:
            return None
        return _normalize_tags(value)


class ChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    article_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int


class ArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content: str
    tags: list[str]
    visibility: ArticleVisibility
    active: bool
    created_by: uuid.UUID | None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: object) -> list[str]:
        return _normalize_tags(value)


class SearchResult(BaseModel):
    """A KB search hit with enough source metadata for future RAG (PRD 7.4)."""

    article_id: uuid.UUID
    title: str
    visibility: ArticleVisibility
    chunk_id: uuid.UUID | None = None
    snippet: str
