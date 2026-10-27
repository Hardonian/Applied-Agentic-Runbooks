"""
Memory and session management for agents.
"""

import json
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

    @abstractmethod
    def get_context(self, session_id: str, limit: int = 10) -> dict[str, Any]:
        """Get conversation context for a session."""

    @abstractmethod
    def get_history(self, session_id: str, limit: int = 50) -> list[Interaction]:
        """Get interaction history for a session."""

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all interactions for a session."""


class SQLiteMemoryStore(MemoryStore):
    """
    SQLite-based memory store for agent sessions.

    Example:
        >>> memory = SQLiteMemoryStore("sessions.db")
        >>> memory.save_interaction("session-123", "Hello", "Hi there!")
        >>> context = memory.get_context("session-123")
    """

    def __init__(self, db_path: str = "agent_sessions.db"):
        """
        Initialize SQLite memory store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                INDEX idx_session_id (session_id),
                INDEX idx_timestamp (timestamp)
            )
        """)

        conn.commit()
        conn.close()

    def save_interaction(
        self,
        session_id: str,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save an interaction to the database."""
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

        # Format as context dictionary
        context = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": interaction.input_text} for interaction in history
            ]
            + [
                {"role": "assistant", "content": interaction.output_text} for interaction in history
            ],
            "count": len(history),
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
            input_text, output_text, timestamp_str, metadata_str = row
            interactions.append(
                Interaction(
                    session_id=session_id,
                    input_text=input_text,
                    output_text=output_text,
                    timestamp=datetime.fromisoformat(timestamp_str),
                    metadata=json.loads(metadata_str) if metadata_str else {},
                )
            )

        # Reverse to get chronological order
        return list(reversed(interactions))

    def clear_session(self, session_id: str) -> None:
        """Clear all interactions for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM interactions WHERE session_id = ?", (session_id,))

        conn.commit()
        conn.close()
