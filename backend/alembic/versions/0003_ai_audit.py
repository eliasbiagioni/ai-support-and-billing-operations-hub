"""ai assist: audit logs

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("tools_called_json", sa.Text(), nullable=False),
        sa.Column("risk_flags_json", sa.Text(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_audit_logs_ticket_id", "ai_audit_logs", ["ticket_id"])
    op.create_index("ix_ai_audit_logs_action_type", "ai_audit_logs", ["action_type"])


def downgrade() -> None:
    op.drop_index("ix_ai_audit_logs_action_type", table_name="ai_audit_logs")
    op.drop_index("ix_ai_audit_logs_ticket_id", table_name="ai_audit_logs")
    op.drop_table("ai_audit_logs")
