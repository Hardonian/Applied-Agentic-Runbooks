"""Add performance indexes

Revision ID: 003
Revises: 002
Create Date: 2024-01-XX 12:00:00.000000

Adds performance indexes for common query patterns:
- Tenant-based queries (tenant_id)
- User-based queries (created_by, user_id)
- Status-based queries (status)
- Timestamp-based queries (created_at, updated_at)
"""


from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes."""
    
    # Indexes for tenant-based queries (multi-tenant isolation)
    op.create_index('ix_agents_tenant_id', 'agents', ['tenant_id'], unique=False)
    op.create_index('ix_workflows_tenant_id', 'workflows', ['tenant_id'], unique=False)
    op.create_index('ix_executions_tenant_id', 'executions', ['tenant_id'], unique=False)
    op.create_index('ix_projects_tenant_id', 'projects', ['tenant_id'], unique=False)
    op.create_index('ix_subscriptions_tenant_id', 'subscriptions', ['tenant_id'], unique=False)
    op.create_index('ix_usage_records_tenant_id', 'usage_records', ['tenant_id'], unique=False)
    
    # Indexes for user-based queries
    op.create_index('ix_agents_created_by', 'agents', ['created_by'], unique=False)
    op.create_index('ix_workflows_created_by', 'workflows', ['created_by'], unique=False)
    op.create_index('ix_executions_created_by', 'executions', ['created_by'], unique=False)
    op.create_index('ix_projects_created_by', 'projects', ['created_by'], unique=False)
    op.create_index('ix_blueprints_publisher_id', 'blueprints', ['publisher_id'], unique=False)
    
    # Indexes for status-based queries
    op.create_index('ix_executions_status', 'executions', ['status'], unique=False)
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'], unique=False)
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'], unique=False)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'], unique=False)
    
    # Composite indexes for common query patterns
    op.create_index('ix_executions_tenant_status', 'executions', ['tenant_id', 'status'], unique=False)
    op.create_index('ix_executions_tenant_created', 'executions', ['tenant_id', 'created_at'], unique=False)
    op.create_index('ix_usage_records_tenant_period', 'usage_records', ['tenant_id', 'period_start', 'period_end'], unique=False)
    
    # Indexes for timestamp-based queries (for cleanup, reporting)
    op.create_index('ix_executions_created_at', 'executions', ['created_at'], unique=False)
    op.create_index('ix_executions_completed_at', 'executions', ['completed_at'], unique=False)
    op.create_index('ix_api_keys_last_used_at', 'api_keys', ['last_used_at'], unique=False)
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'], unique=False)


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop composite indexes
    op.drop_index('ix_usage_records_tenant_period', table_name='usage_records')
    op.drop_index('ix_executions_tenant_created', table_name='executions')
    op.drop_index('ix_executions_tenant_status', table_name='executions')
    
    # Drop timestamp indexes
    op.drop_index('ix_api_keys_expires_at', table_name='api_keys')
    op.drop_index('ix_api_keys_last_used_at', table_name='api_keys')
    op.drop_index('ix_executions_completed_at', table_name='executions')
    op.drop_index('ix_executions_created_at', table_name='executions')
    
    # Drop status indexes
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_api_keys_is_active', table_name='api_keys')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_executions_status', table_name='executions')
    
    # Drop user-based indexes
    op.drop_index('ix_blueprints_publisher_id', table_name='blueprints')
    op.drop_index('ix_projects_created_by', table_name='projects')
    op.drop_index('ix_executions_created_by', table_name='executions')
    op.drop_index('ix_workflows_created_by', table_name='workflows')
    op.drop_index('ix_agents_created_by', table_name='agents')
    
    # Drop tenant-based indexes
    op.drop_index('ix_usage_records_tenant_id', table_name='usage_records')
    op.drop_index('ix_subscriptions_tenant_id', table_name='subscriptions')
    op.drop_index('ix_projects_tenant_id', table_name='projects')
    op.drop_index('ix_executions_tenant_id', table_name='executions')
    op.drop_index('ix_workflows_tenant_id', table_name='workflows')
    op.drop_index('ix_agents_tenant_id', table_name='agents')
