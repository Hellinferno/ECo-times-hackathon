"""add web intel pipeline schema

Revision ID: 9b3c4b2c3e91
Revises: ca475caee2cf
Create Date: 2026-03-27 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b3c4b2c3e91"
down_revision: Union[str, None] = "ca475caee2cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "external_signal_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("strength", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("sentiment", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("dedupe_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_hash", name="uq_external_signal_event_dedupe"),
    )
    op.create_index(op.f("ix_external_signal_events_id"), "external_signal_events", ["id"], unique=False)
    op.create_index(op.f("ix_external_signal_events_symbol"), "external_signal_events", ["symbol"], unique=False)
    op.create_index(op.f("ix_external_signal_events_event_type"), "external_signal_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_external_signal_events_event_time"), "external_signal_events", ["event_time"], unique=False)
    op.create_index(op.f("ix_external_signal_events_expires_at"), "external_signal_events", ["expires_at"], unique=False)
    op.create_index(
        "idx_external_signal_event_symbol_type_time",
        "external_signal_events",
        ["symbol", "event_type", sa.literal_column("event_time DESC")],
        unique=False,
    )

    op.create_table(
        "web_fetch_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("symbols_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index(op.f("ix_web_fetch_runs_id"), "web_fetch_runs", ["id"], unique=False)
    op.create_index(op.f("ix_web_fetch_runs_source_type"), "web_fetch_runs", ["source_type"], unique=False)
    op.create_index(op.f("ix_web_fetch_runs_status"), "web_fetch_runs", ["status"], unique=False)
    op.create_index(op.f("ix_web_fetch_runs_started_at"), "web_fetch_runs", ["started_at"], unique=False)
    op.create_index("idx_web_fetch_runs_started_at", "web_fetch_runs", [sa.literal_column("started_at DESC")], unique=False)

    op.create_table(
        "shadow_signal_diffs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("legacy_score", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("new_score", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("legacy_action", sa.String(length=10), nullable=False),
        sa.Column("new_action", sa.String(length=10), nullable=False),
        sa.Column("diff_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["scan_run_id"], ["scan_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shadow_signal_diffs_id"), "shadow_signal_diffs", ["id"], unique=False)
    op.create_index(op.f("ix_shadow_signal_diffs_scan_run_id"), "shadow_signal_diffs", ["scan_run_id"], unique=False)
    op.create_index(op.f("ix_shadow_signal_diffs_symbol"), "shadow_signal_diffs", ["symbol"], unique=False)
    op.create_index(op.f("ix_shadow_signal_diffs_created_at"), "shadow_signal_diffs", ["created_at"], unique=False)
    op.create_index("idx_shadow_signal_diffs_run_symbol", "shadow_signal_diffs", ["scan_run_id", "symbol"], unique=False)

    op.add_column("scan_results", sa.Column("extra_signals_json", sa.JSON(), nullable=True))
    op.add_column("scan_results", sa.Column("data_quality_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_results", "data_quality_json")
    op.drop_column("scan_results", "extra_signals_json")

    op.drop_index("idx_shadow_signal_diffs_run_symbol", table_name="shadow_signal_diffs")
    op.drop_index(op.f("ix_shadow_signal_diffs_created_at"), table_name="shadow_signal_diffs")
    op.drop_index(op.f("ix_shadow_signal_diffs_symbol"), table_name="shadow_signal_diffs")
    op.drop_index(op.f("ix_shadow_signal_diffs_scan_run_id"), table_name="shadow_signal_diffs")
    op.drop_index(op.f("ix_shadow_signal_diffs_id"), table_name="shadow_signal_diffs")
    op.drop_table("shadow_signal_diffs")

    op.drop_index("idx_web_fetch_runs_started_at", table_name="web_fetch_runs")
    op.drop_index(op.f("ix_web_fetch_runs_started_at"), table_name="web_fetch_runs")
    op.drop_index(op.f("ix_web_fetch_runs_status"), table_name="web_fetch_runs")
    op.drop_index(op.f("ix_web_fetch_runs_source_type"), table_name="web_fetch_runs")
    op.drop_index(op.f("ix_web_fetch_runs_id"), table_name="web_fetch_runs")
    op.drop_table("web_fetch_runs")

    op.drop_index("idx_external_signal_event_symbol_type_time", table_name="external_signal_events")
    op.drop_index(op.f("ix_external_signal_events_expires_at"), table_name="external_signal_events")
    op.drop_index(op.f("ix_external_signal_events_event_time"), table_name="external_signal_events")
    op.drop_index(op.f("ix_external_signal_events_event_type"), table_name="external_signal_events")
    op.drop_index(op.f("ix_external_signal_events_symbol"), table_name="external_signal_events")
    op.drop_index(op.f("ix_external_signal_events_id"), table_name="external_signal_events")
    op.drop_table("external_signal_events")
