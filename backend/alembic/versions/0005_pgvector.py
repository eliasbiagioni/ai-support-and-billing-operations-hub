"""pgvector: knowledge_chunks embedding column + index (Phase 6 RAG)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13

Postgres-only: enables the ``vector`` extension, adds a 1536-d embedding column
to ``knowledge_chunks``, and builds an HNSW cosine index for fast retrieval.
SQLite (tests) creates the equivalent JSON column via the model's with_variant.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Matches Settings.EMBEDDING_DIM (text-embedding-3-small).
_EMBEDDING_DIM = 1536


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"ALTER TABLE knowledge_chunks ADD COLUMN embedding vector({_EMBEDDING_DIM})"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding")
