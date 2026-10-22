"""
Storage backends for prompt logging.
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_factory.promptlog.model import PromptLogEntry, Run


class PromptLogStorage(ABC):
    """Abstract storage interface for prompt logs."""

    @abstractmethod
    def save_run(self, run: Run) -> None:
        """Save a run record."""
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        pass

    @abstractmethod
    def list_runs(self, filters: dict[str, Any] | None = None, limit: int = 100) -> list[Run]:
        """List runs with optional filters."""
        pass

    @abstractmethod
    def save_prompt_entry(self, entry: PromptLogEntry) -> None:
        """Save a prompt log entry."""
        pass

    @abstractmethod
    def get_prompt_entries(self, run_id: str) -> list[PromptLogEntry]:
        """Get all prompt entries for a run."""
        pass


class SQLiteStorage(PromptLogStorage):
    """SQLite storage backend for prompt logs."""

    def __init__(self, db_path: str = "./agent_factory/promptlog.db"):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                agent_id TEXT,
                workflow_id TEXT,
                step_id TEXT,
                inputs TEXT,
                outputs TEXT,
                status TEXT,
                execution_time REAL,
                tokens_used INTEGER,
                cost_estimate REAL,
                timestamp TEXT,
                metadata TEXT
            )
        """)

        # Prompt entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                step INTEGER,
                prompt TEXT,
                response TEXT,
                tool_calls TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)

        conn.commit()
        conn.close()

    def save_run(self, run: Run) -> None:
        """Save a run record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO runs
            (run_id, agent_id, workflow_id, step_id, inputs, outputs, status,
             execution_time, tokens_used, cost_estimate, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run.run_id,
                run.agent_id,
                run.workflow_id,
                run.step_id,
                json.dumps(run.inputs),
                json.dumps(run.outputs),
                run.status,
                run.execution_time,
                run.tokens_used,
                run.cost_estimate,
                run.timestamp.isoformat(),
                json.dumps(run.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def get_run(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Run(
            run_id=row[0],
            agent_id=row[1],
            workflow_id=row[2],
            step_id=row[3],
            inputs=json.loads(row[4]),
            outputs=json.loads(row[5]),
            status=row[6],
            execution_time=row[7],
            tokens_used=row[8],
            cost_estimate=row[9],
            timestamp=datetime.fromisoformat(row[10]),
            metadata=json.loads(row[11]),
        )

    def list_runs(self, filters: dict[str, Any] | None = None, limit: int = 100) -> list[Run]:
        """List runs with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM runs WHERE 1=1"
        params = []

        if filters:
            if "agent_id" in filters:
                query += " AND agent_id = ?"
                params.append(filters["agent_id"])
            if "workflow_id" in filters:
                query += " AND workflow_id = ?"
                params.append(filters["workflow_id"])
            if "status" in filters:
                query += " AND status = ?"
                params.append(filters["status"])

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        runs = []
        for row in rows:
            runs.append(
                Run(
                    run_id=row[0],
                    agent_id=row[1],
                    workflow_id=row[2],
                    step_id=row[3],
                    inputs=json.loads(row[4]),
                    outputs=json.loads(row[5]),
                    status=row[6],
                    execution_time=row[7],
                    tokens_used=row[8],
                    cost_estimate=row[9],
                    timestamp=datetime.fromisoformat(row[10]),
                    metadata=json.loads(row[11]),
                )
            )

        return runs

    def save_prompt_entry(self, entry: PromptLogEntry) -> None:
        """Save a prompt log entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO prompt_entries
            (run_id, step, prompt, response, tool_calls, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry.run_id,
                entry.step,
                entry.prompt,
                entry.response,
                json.dumps(entry.tool_calls),
                entry.timestamp.isoformat(),
                json.dumps(entry.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def get_prompt_entries(self, run_id: str) -> list[PromptLogEntry]:
        """Get all prompt entries for a run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM prompt_entries WHERE run_id = ? ORDER BY step", (run_id,))
        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            entries.append(
                PromptLogEntry(
                    run_id=row[1],
                    step=row[2],
                    prompt=row[3],
                    response=row[4],
                    tool_calls=json.loads(row[5]),
                    timestamp=datetime.fromisoformat(row[6]),
                    metadata=json.loads(row[7]),
                )
            )

        return entries
