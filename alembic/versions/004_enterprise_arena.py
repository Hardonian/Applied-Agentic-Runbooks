"""Add durable Arena runs and authoritative approval tickets.

Revision ID: 004
Revises: 003
"""

import sqlalchemy as sa

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arena_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("benchmark_version", sa.String(), nullable=False),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_arena_runs_tenant_status", "arena_runs", ["tenant_id", "status"])
    op.create_index("ix_arena_runs_tenant_created", "arena_runs", ["tenant_id", "created_at"])
    op.create_table(
        "approval_tickets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("request_hash", sa.String(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("receipt_signature", sa.String(), nullable=True),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_approval_tickets_tenant_status", "approval_tickets", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_approval_tickets_tenant_status", table_name="approval_tickets")
    op.drop_table("approval_tickets")
    op.drop_index("ix_arena_runs_tenant_created", table_name="arena_runs")
    op.drop_index("ix_arena_runs_tenant_status", table_name="arena_runs")
    op.drop_table("arena_runs")
