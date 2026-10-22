"""
Memory and session management for agents.
"""

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Interaction:
    """Represents a single interaction in a session."""

    session_id: str
    input_text: str
    output_text: str
    timestamp: datetime
    metadata: dict[str, Any]


class MemoryStore(ABC):
    """Abstract base class for memory stores."""

    @abstractmethod
    def save_interaction(
        self,
        session_id: str,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an interaction to memory."""
        pass

    @abstractmethod
    def get_context(self, session_id: str, limit: int = 10) -> dict[str, Any]:
        """Get conversation context for a session."""
        pass

    @abstractmethod
    def get_history(self, session_id: str, limit: int = 50) -> list[Interaction]:
        """Get interaction history for a session."""
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all interactions for a session."""
        pass


class SQLiteMemoryStore(MemoryStore):
    """SQLite implementation of memory store."""

    def __init__(self, db_path: str = "./agent_factory/memory.db"):
        """
        Initialize SQLite memory store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON interactions(session_id)")

        conn.commit()
        conn.close()

    def save_interaction(
        self,
        session_id: str,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an interaction to memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO interactions (session_id, input_text, output_text, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                session_id,
                input_text,
                output_text,
                datetime.now().isoformat(),
                json.dumps(metadata or {}),
            ),
        )

        conn.commit()
        conn.close()

    def get_context(self, session_id: str, limit: int = 10) -> dict[str, Any]:
        """Get conversation context for a session."""
        history = self.get_history(session_id, limit)

        context = {
            "recent_interactions": [
                {
                    "input": interaction.input_text,
                    "output": interaction.output_text,
                }
                for interaction in history
            ],
        }

        return context

    def get_history(self, session_id: str, limit: int = 50) -> list[Interaction]:
        """Get interaction history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT input_text, output_text, timestamp, metadata
            FROM interactions
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (session_id, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        interactions = []
        for row in rows:
            interactions.append(
                Interaction(
                    session_id=session_id,
                    input_text=row[0],
                    output_text=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    metadata=json.loads(row[3]) if row[3] else {},
                )
            )

        return list(reversed(interactions))  # Return in chronological order

    def clear_session(self, session_id: str) -> None:
        """Clear all interactions for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM interactions WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()


class RedisMemoryStore(MemoryStore):
    """Redis implementation of memory store."""

    def __init__(self, redis_client=None, key_prefix: str = "agent_memory:"):
        """
        Initialize Redis memory store.

        Args:
            redis_client: Redis client instance (optional, will create if not provided)
            key_prefix: Prefix for Redis keys
        """
        self.key_prefix = key_prefix

        if redis_client:
            self.redis = redis_client
        else:
            try:
                import redis

                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.redis = redis.from_url(redis_url, decode_responses=True)
            except ImportError:
                raise ImportError("redis package is required for RedisMemoryStore") from None
            except Exception as e:
                raise ValueError(f"Failed to connect to Redis: {e}") from e

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"{self.key_prefix}session:{session_id}"

    def _get_interaction_key(self, session_id: str, interaction_id: str) -> str:
        """Get Redis key for interaction."""
        return f"{self.key_prefix}interaction:{session_id}:{interaction_id}"

    def save_interaction(
        self,
        session_id: str,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an interaction to memory."""
        import time
        import uuid

        interaction_id = str(uuid.uuid4())
        interaction_key = self._get_interaction_key(session_id, interaction_id)
        session_key = self._get_session_key(session_id)

        interaction_data = {
            "id": interaction_id,
            "input_text": input_text,
            "output_text": output_text,
            "timestamp": datetime.now().isoformat(),
            "metadata": json.dumps(metadata or {}),
        }

        # Store interaction
        self.redis.hset(interaction_key, mapping=interaction_data)

        # Add to session list (sorted set by timestamp)
        timestamp = time.time()
        self.redis.zadd(session_key, {interaction_id: timestamp})

        # Set expiration (30 days default)
        self.redis.expire(session_key, 30 * 24 * 60 * 60)
        self.redis.expire(interaction_key, 30 * 24 * 60 * 60)

    def get_context(self, session_id: str, limit: int = 10) -> dict[str, Any]:
        """Get conversation context for a session."""
        history = self.get_history(session_id, limit)

        context = {
            "recent_interactions": [
                {
                    "input": interaction.input_text,
                    "output": interaction.output_text,
                }
                for interaction in history
            ],
        }

        return context

    def get_history(self, session_id: str, limit: int = 50) -> list[Interaction]:
        """Get interaction history for a session."""
        session_key = self._get_session_key(session_id)

        # Get interaction IDs from sorted set (most recent first)
        interaction_ids = self.redis.zrevrange(session_key, 0, limit - 1)

        interactions = []
        for interaction_id in interaction_ids:
            interaction_key = self._get_interaction_key(session_id, interaction_id)
            data = self.redis.hgetall(interaction_key)

            if data:
                interactions.append(
                    Interaction(
                        session_id=session_id,
                        input_text=data.get("input_text", ""),
                        output_text=data.get("output_text", ""),
                        timestamp=datetime.fromisoformat(
                            data.get("timestamp", datetime.now().isoformat())
                        ),
                        metadata=json.loads(data.get("metadata", "{}")),
                    )
                )

        return list(reversed(interactions))  # Return in chronological order

    def clear_session(self, session_id: str) -> None:
        """Clear all interactions for a session."""
        session_key = self._get_session_key(session_id)

        # Get all interaction IDs
        interaction_ids = self.redis.zrange(session_key, 0, -1)

        # Delete all interactions
        for interaction_id in interaction_ids:
            interaction_key = self._get_interaction_key(session_id, interaction_id)
            self.redis.delete(interaction_key)

        # Delete session key
        self.redis.delete(session_key)


def get_memory_store(store_type: str = "sqlite", **kwargs) -> MemoryStore:
    """
    Get memory store instance.

    Args:
        store_type: Type of store ("sqlite" or "redis")
        **kwargs: Additional arguments for store initialization

    Returns:
        MemoryStore instance
    """
    if store_type == "sqlite":
        db_path = kwargs.get("db_path", "./agent_factory/memory.db")
        return SQLiteMemoryStore(db_path=db_path)
    elif store_type == "redis":
        redis_client = kwargs.get("redis_client")
        key_prefix = kwargs.get("key_prefix", "agent_memory:")
        return RedisMemoryStore(redis_client=redis_client, key_prefix=key_prefix)
    else:
        raise ValueError(f"Unknown memory store type: {store_type}")
