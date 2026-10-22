"""Master schema migration

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

This migration consolidates all schema changes into a single coherent migration
that matches the SQLAlchemy models exactly. It replaces the incomplete initial
migration and adds missing tables (projects, plans, subscriptions, usage_records).

For new installations, apply this migration directly.
For existing installations, this migration will add missing tables and fix schema inconsistencies.
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema to match models."""
    
    # Check if tables exist (for fresh installs, they won't exist yet)
    # Use connection to check table existence
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Fix existing tables to match models (only if they exist)
    
    if 'agents' in existing_tables:
        # Fix agents table: rename user_id to created_by if it exists
        columns = [col['name'] for col in inspector.get_columns('agents')]
        if 'user_id' in columns and 'created_by' not in columns:
            op.alter_column('agents', 'user_id', new_column_name='created_by', existing_type=sa.String())
    
    if 'blueprints' in existing_tables:
        # Fix blueprints table: add missing marketplace fields
        columns = [col['name'] for col in inspector.get_columns('blueprints')]
        if 'pricing_model' not in columns:
            op.add_column('blueprints', sa.Column('pricing_model', sa.String(), server_default='free'))
        if 'price' not in columns:
            op.add_column('blueprints', sa.Column('price', sa.Float(), server_default='0.0'))
        if 'publisher_id' not in columns:
            op.add_column('blueprints', sa.Column('publisher_id', sa.String(), sa.ForeignKey('users.id'), nullable=True))
        if 'is_public' not in columns:
            op.add_column('blueprints', sa.Column('is_public', sa.Boolean(), server_default='false'))
        if 'downloads' not in columns:
            op.add_column('blueprints', sa.Column('downloads', sa.Integer(), server_default='0'))
        if 'rating' not in columns:
            op.add_column('blueprints', sa.Column('rating', sa.Float(), server_default='0.0'))
        if 'reviews_count' not in columns:
            op.add_column('blueprints', sa.Column('reviews_count', sa.Integer(), server_default='0'))
    
    if 'executions' in existing_tables:
        # Fix executions table: rename columns to match model
        columns = [col['name'] for col in inspector.get_columns('executions')]
        if 'type' in columns and 'execution_type' not in columns:
            op.alter_column('executions', 'type', new_column_name='execution_type', existing_type=sa.String())
        if 'entity_id' in columns and 'resource_id' not in columns:
            op.alter_column('executions', 'entity_id', new_column_name='resource_id', existing_type=sa.String())
        if 'result' in columns and 'output_data' not in columns:
            op.alter_column('executions', 'result', new_column_name='output_data', existing_type=sa.JSON())
        if 'input_data' not in columns:
            op.add_column('executions', sa.Column('input_data', sa.JSON(), nullable=True))
        if 'execution_time' not in columns:
            op.add_column('executions', sa.Column('execution_time', sa.Float(), nullable=True))
        if 'user_id' in columns and 'created_by' not in columns:
            op.alter_column('executions', 'user_id', new_column_name='created_by', existing_type=sa.String())
    
    if 'audit_logs' in existing_tables:
        # Fix audit_logs table: change id to autoincrement integer, rename metadata to details, add ip_address
        # This is complex - we'll create a new table and migrate data
        columns = [col['name'] for col in inspector.get_columns('audit_logs')]
        
        # Check if id is string type (old) or integer (already migrated)
        col_info = next((col for col in inspector.get_columns('audit_logs') if col['name'] == 'id'), None)
        if col_info:
            # Check if we need to migrate (id is string or metadata exists)
            needs_migration = (
                str(col_info['type']).startswith('VARCHAR') or 
                str(col_info['type']).startswith('TEXT') or
                'metadata' in columns
            )
            
            if needs_migration:
                op.create_table(
                    'audit_logs_new',
                    sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
                    sa.Column('event_type', sa.String(), nullable=False),
                    sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
                    sa.Column('resource_type', sa.String(), nullable=True),
                    sa.Column('resource_id', sa.String(), nullable=True),
                    sa.Column('action', sa.String(), nullable=True),
                    sa.Column('success', sa.Boolean(), server_default='true'),
                    sa.Column('details', sa.JSON(), nullable=True),
                    sa.Column('ip_address', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                )
                op.create_index('ix_audit_logs_created_at', 'audit_logs_new', ['created_at'])
                
                # Migrate data from old table to new
                op.execute("""
                    INSERT INTO audit_logs_new (event_type, user_id, resource_type, resource_id, action, success, details, created_at)
                    SELECT event_type, user_id, resource_type, resource_id, action, COALESCE(success, true), COALESCE(metadata, '{}'::json), created_at
                    FROM audit_logs
                """)
                
                # Drop old table and rename new
                op.drop_table('audit_logs')
                op.rename_table('audit_logs_new', 'audit_logs')
        else:
            # Just add missing columns if id is already integer
            if 'details' not in columns and 'metadata' in columns:
                op.alter_column('audit_logs', 'metadata', new_column_name='details', existing_type=sa.JSON())
            if 'ip_address' not in columns:
                op.add_column('audit_logs', sa.Column('ip_address', sa.String(), nullable=True))
            if 'ix_audit_logs_created_at' not in [idx['name'] for idx in inspector.get_indexes('audit_logs')]:
                op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Create missing tables (only if they don't exist)
    
    # Projects table
    if 'projects' not in existing_tables:
        op.create_table(
        'projects',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('project_type', sa.String(), server_default='saas_app'),
        sa.Column('tenant_id', sa.String(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('created_by', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('config', sa.JSON(), server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    
    # Plans table
    if 'plans' not in existing_tables:
        op.create_table(
        'plans',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('plan_type', sa.String(), nullable=False),
        sa.Column('price_monthly', sa.Float(), server_default='0.0'),
        sa.Column('price_yearly', sa.Float(), server_default='0.0'),
        sa.Column('currency', sa.String(), server_default='USD'),
        sa.Column('features', sa.JSON(), server_default='{}'),
        sa.Column('limits', sa.JSON(), server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    
    # Subscriptions table
    if 'subscriptions' not in existing_tables:
        op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.String(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('plan_id', sa.String(), sa.ForeignKey('plans.id'), nullable=False),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('billing_cycle', sa.String(), server_default='monthly'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    
    # Usage records table
    if 'usage_records' not in existing_tables:
        op.create_table(
        'usage_records',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.String(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('subscription_id', sa.String(), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('billing_unit', sa.String(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), server_default='0.0'),
        sa.Column('total_cost', sa.Float(), server_default='0.0'),
        sa.Column('currency', sa.String(), server_default='USD'),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop new tables
    op.drop_table('usage_records')
    op.drop_table('subscriptions')
    op.drop_table('plans')
    op.drop_table('projects')
    
    # Revert audit_logs changes
    op.create_table(
        'audit_logs_old',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('success', sa.Boolean(), server_default='true'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    
    op.execute("""
        INSERT INTO audit_logs_old (id, event_type, user_id, resource_type, resource_id, action, success, metadata, created_at)
        SELECT id::text, event_type, user_id, resource_type, resource_id, action, success, details, created_at
        FROM audit_logs
    """)
    
    op.drop_table('audit_logs')
    op.rename_table('audit_logs_old', 'audit_logs')
    
    # Revert executions changes
    op.alter_column('executions', 'created_by', new_column_name='user_id', existing_type=sa.String())
    op.drop_column('executions', 'execution_time')
    op.drop_column('executions', 'input_data')
    op.alter_column('executions', 'output_data', new_column_name='result', existing_type=sa.JSON())
    op.alter_column('executions', 'resource_id', new_column_name='entity_id', existing_type=sa.String())
    op.alter_column('executions', 'execution_type', new_column_name='type', existing_type=sa.String())
    
    # Revert blueprints changes
    op.drop_column('blueprints', 'reviews_count')
    op.drop_column('blueprints', 'rating')
    op.drop_column('blueprints', 'downloads')
    op.drop_column('blueprints', 'is_public')
    op.drop_column('blueprints', 'publisher_id')
    op.drop_column('blueprints', 'price')
    op.drop_column('blueprints', 'pricing_model')
    
    # Revert agents changes
    op.alter_column('agents', 'created_by', new_column_name='user_id', existing_type=sa.String())
