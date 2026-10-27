"""Database session management."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL") or ""
if not DATABASE_URL:
    # A local checkout must be runnable without an accidental network call to
    # localhost Postgres. Production validation requires DATABASE_URL, while
    # development defaults to a durable local SQLite database.
    DATABASE_URL = "sqlite:///./agent_factory.db"

# Optimize connection pooling for Supabase
# Supabase recommends connection pooling with pgbouncer
# Use transaction mode for best compatibility
is_supabase = os.getenv("SUPABASE_URL") is not None

if is_supabase:
    # Supabase connection pooling settings
    # Use connection pooler if available (port 6543), otherwise direct (port 5432)
    database_url = DATABASE_URL
    if ":5432/" in database_url:
        # Try to use connection pooler (port 6543)
        # Note: Supabase provides both direct and pooled connections
        # Direct: port 5432, Pooled: port 6543
        # For production, prefer pooled connections
        pooler_url = database_url.replace(":5432/", ":6543/")
        # Use pooler if SUPABASE_USE_POOLER is set, otherwise direct
        if os.getenv("SUPABASE_USE_POOLER", "true").lower() == "true":
            database_url = pooler_url

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,  # Smaller pool for Supabase (they handle scaling)
        max_overflow=10,
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "sslmode": "require",  # Supabase requires SSL
        },
    )
else:
    # Standard PostgreSQL connection settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
Base.__allow_unmapped__ = True


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_url() -> str:
    """Get database URL from environment."""
    return DATABASE_URL


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
