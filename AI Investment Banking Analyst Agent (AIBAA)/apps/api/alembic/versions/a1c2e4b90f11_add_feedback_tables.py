"""add feedback tables

Revision ID: a1c2e4b90f11
Revises: 7a6cb59e0d64
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c2e4b90f11"
down_revision: Union[str, Sequence[str], None] = "7a6cb59e0d64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback_threads",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.String(), nullable=False, index=True),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "feedback_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False, index=True),
        sa.Column("author_user_id", sa.String(), nullable=False, index=True),
        sa.Column("author_role", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.ForeignKeyConstraint(["thread_id"], ["feedback_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("feedback_messages")
    op.drop_table("feedback_threads")
