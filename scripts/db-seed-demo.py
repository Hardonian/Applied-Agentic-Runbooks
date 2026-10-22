#!/usr/bin/env python3
"""
Seed database with demo data for testing and demos.

Usage:
    python scripts/db-seed-demo.py

Environment:
    DATABASE_URL: PostgreSQL connection string
"""

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agent_factory.database.models import (
    Agent,
    Blueprint,
    Execution,
    Plan,
    Project,
    Subscription,
    Tenant,
    User,
    Workflow,
)
from agent_factory.database.session import get_database_url


def create_demo_data(session):
    """Create demo data."""
    print("Creating demo data...")
    
    # Create demo tenant
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(
        id=tenant_id,
        name="Demo Organization",
        slug="demo-org",
        is_active=True,
        plan="pro",
        resource_quota={"agents": 50, "workflows": 20},
        usage={"agents": 0, "workflows": 0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(tenant)
    print(f"  ✓ Created tenant: {tenant.name}")
    
    # Create demo user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="demo@example.com",
        hashed_password="$2b$12$demo",  # Demo password hash
        is_active=True,
        is_superuser=False,
        tenant_id=tenant_id,
        roles=["user"],
        permissions=["read", "write"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user)
    print(f"  ✓ Created user: {user.email}")
    
    # Create demo agent
    agent_id = str(uuid.uuid4())
    agent = Agent(
        id=agent_id,
        name="Demo Assistant",
        instructions="You are a helpful assistant that answers questions and helps with tasks.",
        model="gpt-4o",
        tenant_id=tenant_id,
        created_by=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(agent)
    print(f"  ✓ Created agent: {agent.name}")
    
    # Create demo workflow
    workflow_id = str(uuid.uuid4())
    workflow = Workflow(
        id=workflow_id,
        name="Demo Workflow",
        definition={
            "steps": [
                {"agent": agent_id, "action": "process"},
                {"agent": agent_id, "action": "respond"}
            ]
        },
        tenant_id=tenant_id,
        created_by=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(workflow)
    print(f"  ✓ Created workflow: {workflow.name}")
    
    # Create demo blueprint
    blueprint_id = str(uuid.uuid4())
    blueprint = Blueprint(
        id=blueprint_id,
        name="Demo Blueprint",
        description="A demo blueprint for testing",
        version="1.0.0",
        definition={
            "agent": {
                "name": "Demo Agent",
                "instructions": "Help users with questions"
            }
        },
        pricing_model="free",
        price=0.0,
        publisher_id=user_id,
        is_public=True,
        downloads=0,
        rating=0.0,
        reviews_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(blueprint)
    print(f"  ✓ Created blueprint: {blueprint.name}")
    
    # Create demo execution
    execution_id = str(uuid.uuid4())
    execution = Execution(
        id=execution_id,
        execution_type="agent",
        resource_id=agent_id,
        status="completed",
        input_data={"message": "Hello, world!"},
        output_data={"response": "Hello! How can I help you?"},
        execution_time=1.5,
        tenant_id=tenant_id,
        created_by=user_id,
        created_at=datetime.utcnow() - timedelta(hours=1),
        completed_at=datetime.utcnow() - timedelta(hours=1)
    )
    session.add(execution)
    print("  ✓ Created execution record")
    
    # Create demo project
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        name="Demo Project",
        project_type="saas_app",
        tenant_id=tenant_id,
        created_by=user_id,
        config={"theme": "default"},
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(project)
    print(f"  ✓ Created project: {project.name}")
    
    # Create demo plan
    plan_id = str(uuid.uuid4())
    plan = Plan(
        id=plan_id,
        name="Pro Plan",
        plan_type="pro",
        price_monthly=29.99,
        price_yearly=299.99,
        currency="USD",
        features={"agents": 50, "workflows": 20, "support": "email"},
        limits={"api_calls": 10000, "storage_gb": 10},
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(plan)
    print(f"  ✓ Created plan: {plan.name}")
    
    # Create demo subscription
    subscription_id = str(uuid.uuid4())
    subscription = Subscription(
        id=subscription_id,
        tenant_id=tenant_id,
        plan_id=plan_id,
        status="active",
        billing_cycle="monthly",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(subscription)
    print("  ✓ Created subscription")
    
    session.commit()
    print()
    print("=" * 60)
    print("✓ Demo data created successfully!")
    print("=" * 60)
    print()
    print("Demo credentials:")
    print(f"  Tenant: {tenant.slug}")
    print(f"  User: {user.email}")
    print(f"  Agent ID: {agent_id}")
    print(f"  Workflow ID: {workflow_id}")
    print()


def main():
    """Main function."""
    db_url = get_database_url()
    
    if not db_url:
        print("❌ Error: DATABASE_URL not set")
        print("Set DATABASE_URL environment variable")
        sys.exit(1)
    
    print("Connecting to database...")
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 10})
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    print("✓ Connected")
    print()
    
    try:
        # Check if demo data already exists
        existing_tenant = session.query(Tenant).filter_by(slug="demo-org").first()
        if existing_tenant:
            print("⚠️  Demo data already exists. Skipping seed.")
            print("To recreate, delete the demo tenant first.")
            return
        
        create_demo_data(session)
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    main()
