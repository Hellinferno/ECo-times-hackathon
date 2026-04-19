"""add feedback tables and merge web-intel + unified-platform heads

Revision ID: b7f3a12d4e80
Revises: 9b3c4b2c3e91, 20260328_unified
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7f3a12d4e80"
down_revision: Union[str, Sequence[str], None] = ("9b3c4b2c3e91", "20260328_unified")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback_threads",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["platform_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feedback_threads_org_id"), "feedback_threads", ["org_id"], unique=False)
    op.create_index(
        op.f("ix_feedback_threads_created_by_user_id"),
        "feedback_threads",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(op.f("ix_feedback_threads_status"), "feedback_threads", ["status"], unique=False)
    op.create_index(
        op.f("ix_feedback_threads_last_activity_at"),
        "feedback_threads",
        ["last_activity_at"],
        unique=False,
    )

    op.create_table(
        "feedback_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=False),
        sa.Column("author_role", sa.String(length=40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["feedback_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["platform_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feedback_messages_thread_id"),
        "feedback_messages",
        ["thread_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feedback_messages_author_user_id"),
        "feedback_messages",
        ["author_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feedback_messages_created_at"),
        "feedback_messages",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_messages_created_at"), table_name="feedback_messages")
    op.drop_index(op.f("ix_feedback_messages_author_user_id"), table_name="feedback_messages")
    op.drop_index(op.f("ix_feedback_messages_thread_id"), table_name="feedback_messages")
    op.drop_table("feedback_messages")

    op.drop_index(op.f("ix_feedback_threads_last_activity_at"), table_name="feedback_threads")
    op.drop_index(op.f("ix_feedback_threads_status"), table_name="feedback_threads")
    op.drop_index(op.f("ix_feedback_threads_created_by_user_id"), table_name="feedback_threads")
    op.drop_index(op.f("ix_feedback_threads_org_id"), table_name="feedback_threads")
    op.drop_table("feedback_threads")
