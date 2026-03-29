"""Unified platform schema - companies, workspaces, valuations, documents, outputs

Revision ID: 20260328_unified
Revises: ca475caee2cf
Create Date: 2026-03-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260328_unified'
down_revision: Union[str, None] = 'ca475caee2cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Organizations
    op.create_table('organizations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # Platform Users
    op.create_table('platform_users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('org_id', sa.String(length=36), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('role', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('org_id', 'username')
    )
    op.create_index(op.f('ix_platform_users_id'), 'platform_users', ['id'], unique=False)
    op.create_index(op.f('ix_platform_users_org_id'), 'platform_users', ['org_id'], unique=False)

    # Companies
    op.create_table('companies',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('stock_id', sa.Integer(), nullable=True),
    sa.Column('symbol', sa.String(length=20), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('sector', sa.String(length=120), nullable=True),
    sa.Column('listing_status', sa.String(length=40), nullable=False),
    sa.Column('exchange', sa.String(length=20), nullable=True),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('market_cap', sa.Numeric(precision=16, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_symbol'), 'companies', ['symbol'], unique=False)
    op.create_index(op.f('ix_companies_sector'), 'companies', ['sector'], unique=False)

    # Workspaces
    op.create_table('workspaces',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('org_id', sa.String(length=36), nullable=False),
    sa.Column('owner_id', sa.String(length=36), nullable=False),
    sa.Column('company_id', sa.String(length=36), nullable=False),
    sa.Column('workspace_type', sa.String(length=40), nullable=False),
    sa.Column('title', sa.String(length=180), nullable=False),
    sa.Column('stage', sa.String(length=40), nullable=False),
    sa.Column('source_symbol', sa.String(length=20), nullable=True),
    sa.Column('source_decision_id', sa.String(length=40), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('health_summary', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['platform_users.id'], ),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)
    op.create_index(op.f('ix_workspaces_org_id'), 'workspaces', ['org_id'], unique=False)
    op.create_index(op.f('ix_workspaces_owner_id'), 'workspaces', ['owner_id'], unique=False)
    op.create_index(op.f('ix_workspaces_company_id'), 'workspaces', ['company_id'], unique=False)
    op.create_index(op.f('ix_workspaces_workspace_type'), 'workspaces', ['workspace_type'], unique=False)
    op.create_index(op.f('ix_workspaces_stage'), 'workspaces', ['stage'], unique=False)

    # Workspace Documents
    op.create_table('workspace_documents',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('uploaded_by', sa.String(length=36), nullable=False),
    sa.Column('filename', sa.String(length=200), nullable=False),
    sa.Column('file_type', sa.String(length=20), nullable=False),
    sa.Column('file_size_bytes', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=60), nullable=True),
    sa.Column('classification', sa.String(length=40), nullable=False),
    sa.Column('parse_status', sa.String(length=40), nullable=False),
    sa.Column('rag_status', sa.String(length=40), nullable=False),
    sa.Column('storage_path', sa.String(length=400), nullable=True),
    sa.Column('text_preview', sa.Text(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by'], ['platform_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_documents_id'), 'workspace_documents', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_documents_workspace_id'), 'workspace_documents', ['workspace_id'], unique=False)

    # Workspace Agent Runs
    op.create_table('workspace_agent_runs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('requested_by', sa.String(length=36), nullable=False),
    sa.Column('agent_type', sa.String(length=40), nullable=False),
    sa.Column('task_name', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('parameters_json', sa.JSON(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.ForeignKeyConstraint(['requested_by'], ['platform_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_agent_runs_id'), 'workspace_agent_runs', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_agent_runs_workspace_id'), 'workspace_agent_runs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_workspace_agent_runs_agent_type'), 'workspace_agent_runs', ['agent_type'], unique=False)
    op.create_index(op.f('ix_workspace_agent_runs_status'), 'workspace_agent_runs', ['status'], unique=False)

    # Valuation Runs
    op.create_table('valuation_runs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('requested_by', sa.String(length=36), nullable=False),
    sa.Column('model_type', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('assumptions_json', sa.JSON(), nullable=False),
    sa.Column('result_summary_json', sa.JSON(), nullable=True),
    sa.Column('warnings_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.ForeignKeyConstraint(['requested_by'], ['platform_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_valuation_runs_id'), 'valuation_runs', ['id'], unique=False)
    op.create_index(op.f('ix_valuation_runs_workspace_id'), 'valuation_runs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_valuation_runs_model_type'), 'valuation_runs', ['model_type'], unique=False)
    op.create_index(op.f('ix_valuation_runs_status'), 'valuation_runs', ['status'], unique=False)

    # Workspace Outputs
    op.create_table('workspace_outputs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('source_run_id', sa.String(length=36), nullable=True),
    sa.Column('source_kind', sa.String(length=40), nullable=False),
    sa.Column('output_type', sa.String(length=40), nullable=False),
    sa.Column('review_status', sa.String(length=40), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('preview_markdown', sa.Text(), nullable=True),
    sa.Column('storage_path', sa.String(length=400), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_outputs_id'), 'workspace_outputs', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_outputs_workspace_id'), 'workspace_outputs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_workspace_outputs_output_type'), 'workspace_outputs', ['output_type'], unique=False)
    op.create_index(op.f('ix_workspace_outputs_review_status'), 'workspace_outputs', ['review_status'], unique=False)

    # Workspace Tasks
    op.create_table('workspace_tasks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=180), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('priority', sa.String(length=40), nullable=False),
    sa.Column('owner_label', sa.String(length=80), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('due_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_tasks_id'), 'workspace_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_tasks_workspace_id'), 'workspace_tasks', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_workspace_tasks_status'), 'workspace_tasks', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('workspace_tasks')
    op.drop_table('workspace_outputs')
    op.drop_table('valuation_runs')
    op.drop_table('workspace_agent_runs')
    op.drop_table('workspace_documents')
    op.drop_table('workspaces')
    op.drop_table('companies')
    op.drop_table('platform_users')
    op.drop_table('organizations')
