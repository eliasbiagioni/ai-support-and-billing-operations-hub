"""copilot: persisted conversations + messages (WebSocket)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-14

Adds ``copilot_conversations`` and ``copilot_messages`` so the Billing Copilot
can replay full history to the LLM and restore transcripts after reconnect.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilot_conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_copilot_conversations_user_id", "copilot_conversations", ["user_id"]
    )

    op.create_table(
        "copilot_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tools_called_json", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.Text(), nullable=False),
        sa.Column("proposed_actions_json", sa.Text(), nullable=False),
        sa.Column("risk_flags_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["copilot_conversations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_copilot_messages_conversation_id", "copilot_messages", ["conversation_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_copilot_messages_conversation_id", table_name="copilot_messages"
    )
    op.drop_table("copilot_messages")
    op.drop_index(
        "ix_copilot_conversations_user_id", table_name="copilot_conversations"
    )
    op.drop_table("copilot_conversations")
