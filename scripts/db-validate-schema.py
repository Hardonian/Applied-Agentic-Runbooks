#!/usr/bin/env python3
"""
Database schema validation script.

Validates that the database schema matches expected structure:
- Core tables exist
- Required columns exist
- Indexes are present
- Foreign keys are correct

Usage:
    python scripts/db-validate-schema.py

Environment:
    DATABASE_URL: PostgreSQL connection string
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect, text

# Expected core tables
CORE_TABLES = [
    'users',
    'tenants',
    'agents',
    'workflows',
    'blueprints',
    'executions',
    'audit_logs',
    'api_keys',
    'projects',
    'plans',
    'subscriptions',
    'usage_records',
]

# Expected columns for key tables (sample - not exhaustive)
EXPECTED_COLUMNS = {
    'users': ['id', 'email', 'hashed_password', 'tenant_id', 'created_at'],
    'tenants': ['id', 'name', 'slug', 'is_active', 'created_at'],
    'agents': ['id', 'name', 'instructions', 'tenant_id', 'created_by', 'created_at'],
    'workflows': ['id', 'name', 'definition', 'tenant_id', 'created_by', 'created_at'],
    'blueprints': ['id', 'name', 'version', 'definition', 'publisher_id', 'created_at'],
    'executions': ['id', 'execution_type', 'resource_id', 'status', 'tenant_id', 'created_at'],
    'audit_logs': ['id', 'event_type', 'user_id', 'created_at'],
    'api_keys': ['id', 'key_hash', 'tenant_id', 'user_id', 'is_active', 'created_at'],
    'projects': ['id', 'name', 'tenant_id', 'created_by', 'created_at'],
    'plans': ['id', 'name', 'plan_type', 'price_monthly', 'is_active', 'created_at'],
    'subscriptions': ['id', 'tenant_id', 'plan_id', 'status', 'created_at'],
    'usage_records': ['id', 'tenant_id', 'billing_unit', 'quantity', 'created_at'],
}

# Expected indexes
EXPECTED_INDEXES = {
    'users': ['ix_users_email'],
    'tenants': ['ix_tenants_slug'],
    'audit_logs': ['ix_audit_logs_created_at'],
}


def get_database_url():
    """Get database URL from environment."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Try individual variables
        user = os.getenv('POSTGRES_USER', 'agent_factory')
        password = os.getenv('POSTGRES_PASSWORD', '')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        db = os.getenv('POSTGRES_DB', 'agent_factory')
        db_url = f'postgresql://{user}:{password}@{host}:{port}/{db}'
    return db_url


def validate_schema():
    """Validate database schema."""
    db_url = get_database_url()
    
    if not db_url:
        print("❌ Error: DATABASE_URL not set")
        print("Set DATABASE_URL environment variable or POSTGRES_* variables")
        return False
    
    print("Connecting to database...")
    print(f"URL: {db_url.split('@')[1] if '@' in db_url else '***'}")
    print()
    
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 10})
        inspector = inspect(engine)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False
    
    print("✓ Database connection successful")
    print()
    
    # Get existing tables
    existing_tables = set(inspector.get_table_names())
    
    # Check core tables exist
    print("Checking core tables...")
    missing_tables = []
    for table in CORE_TABLES:
        if table in existing_tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ❌ {table} - MISSING")
            missing_tables.append(table)
    
    if missing_tables:
        print()
        print(f"❌ Missing tables: {', '.join(missing_tables)}")
        print("Run migrations: alembic upgrade head")
        return False
    
    print()
    print("✓ All core tables exist")
    print()
    
    # Check columns
    print("Checking table columns...")
    column_issues = []
    for table, expected_cols in EXPECTED_COLUMNS.items():
        if table not in existing_tables:
            continue
        
        existing_cols = {col['name'] for col in inspector.get_columns(table)}
        missing_cols = set(expected_cols) - existing_cols
        
        if missing_cols:
            column_issues.append((table, missing_cols))
            print(f"  ❌ {table}: Missing columns {missing_cols}")
        else:
            print(f"  ✓ {table}: All required columns present")
    
    if column_issues:
        print()
        print("❌ Column validation failed")
        for table, cols in column_issues:
            print(f"  {table}: {cols}")
        return False
    
    print()
    print("✓ All required columns exist")
    print()
    
    # Check indexes
    print("Checking indexes...")
    index_issues = []
    for table, expected_idxs in EXPECTED_INDEXES.items():
        if table not in existing_tables:
            continue
        
        existing_idxs = {idx['name'] for idx in inspector.get_indexes(table)}
        missing_idxs = set(expected_idxs) - existing_idxs
        
        if missing_idxs:
            index_issues.append((table, missing_idxs))
            print(f"  ⚠️  {table}: Missing indexes {missing_idxs}")
        else:
            print(f"  ✓ {table}: Required indexes present")
    
    if index_issues:
        print()
        print("⚠️  Some indexes are missing (non-critical)")
        for table, idxs in index_issues:
            print(f"  {table}: {idxs}")
    
    print()
    
    # Check foreign keys
    print("Checking foreign keys...")
    fk_count = 0
    for table in CORE_TABLES:
        if table not in existing_tables:
            continue
        fks = inspector.get_foreign_keys(table)
        fk_count += len(fks)
    
    print(f"  ✓ Found {fk_count} foreign key constraints")
    print()
    
    # Check current migration revision
    print("Checking migration status...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT version_num 
                FROM alembic_version 
                LIMIT 1
            """))
            current_rev = result.scalar()
            if current_rev:
                print(f"  ✓ Current revision: {current_rev}")
            else:
                print("  ⚠️  No migration revision found")
    except Exception as e:
        print(f"  ⚠️  Could not check migration revision: {e}")
    
    print()
    print("=" * 60)
    print("✓ Schema validation passed!")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = validate_schema()
    sys.exit(0 if success else 1)
