"""Backfill embeddings for knowledge chunks that are missing them (Phase 6 RAG).

Run after configuring OPENAI_API_KEY (and running migrations) with:
    python -m app.commands.backfill_embeddings
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.integrations.llm_client import get_optional_llm_client
from app.services.knowledge_service import KnowledgeService

logger = get_logger(__name__)


def backfill() -> None:
    llm = get_optional_llm_client()
    if llm is None:
        logger.error("OPENAI_API_KEY is not set; cannot compute embeddings.")
        return
    with SessionLocal() as db:
        updated = KnowledgeService(db, llm).backfill_embeddings()
        logger.info("Backfilled embeddings for %d chunks.", updated)


if __name__ == "__main__":
    backfill()
