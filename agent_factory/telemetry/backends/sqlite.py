"""
SQLite backend for telemetry storage.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.model import TelemetryEvent, EventType


class SQLiteTelemetryBackend(TelemetryBackend):
    """
    SQLite storage backend for telemetry events.
    
    Suitable for local development and small deployments.
    """
    
    def __init__(self, db_path: str = "./agent_factory/telemetry.db"):
        """
        Initialize SQLite telemetry backend.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        # SQLite creates a separate in-memory database per connection.  Keep
        # one connection alive for the documented ``:memory:`` test/local use
        # case so initialization, writes, and queries address the same store.
        self._memory_connection = (
            sqlite3.connect(":memory:") if str(db_path) == ":memory:" else None
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Return the backing connection without splitting in-memory state."""
        return self._memory_connection or sqlite3.connect(self.db_path)

    def _close(self, conn: sqlite3.Connection) -> None:
        """Close file-backed connections while retaining an in-memory store."""
        if conn is not self._memory_connection:
            conn.close()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Main events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tenant_id TEXT,
                user_id TEXT,
                project_id TEXT,
                event_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_tenant 
            ON telemetry_events(tenant_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_type 
            ON telemetry_events(event_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp 
            ON telemetry_events(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_user 
            ON telemetry_events(user_id)
        """)
        
        conn.commit()
        self._close(conn)
    
    def store_event(self, event: TelemetryEvent) -> None:
        """Store a telemetry event."""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            event_data = json.dumps(event.to_dict())
            
            cursor.execute("""
                INSERT OR REPLACE INTO telemetry_events 
                (event_id, event_type, timestamp, tenant_id, user_id, project_id, event_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_type.value,
                event.timestamp.isoformat(),
                event.tenant_id,
                event.user_id,
                event.project_id,
                event_data,
            ))
            
            conn.commit()
        finally:
            self._close(conn)
    
    def query_events(
        self,
        event_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TelemetryEvent]:
        """Query telemetry events."""
        conn = self._connect()
        cursor = conn.cursor()
        
        try:
            query = "SELECT event_data FROM telemetry_events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for (event_data_json,) in rows:
                event_dict = json.loads(event_data_json)
                # Reconstruct event object based on event_type
                event = self._deserialize_event(event_dict)
                if event:
                    events.append(event)
            
            return events
        finally:
            self._close(conn)
    
    def _deserialize_event(self, event_dict: dict) -> Optional[TelemetryEvent]:
        """Deserialize event from dictionary."""
        event_type_str = event_dict.get("event_type")
        
        if not event_type_str:
            return None
        
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            return None
        
        # Import event classes
        from agent_factory.telemetry.model import (
            AgentRunEvent,
            WorkflowRunEvent,
            BlueprintInstallEvent,
            ErrorEvent,
            BillingUsageEvent,
            TenantEvent,
            ProjectEvent,
            UserActivatedEvent,
            ReferralEvent,
            RevenueEvent,
            UserSignupEvent,
            UserLoginEvent,
        )
        
        # Map event types to classes
        event_classes = {
            EventType.AGENT_RUN: AgentRunEvent,
            EventType.WORKFLOW_RUN: WorkflowRunEvent,
            EventType.BLUEPRINT_INSTALL: BlueprintInstallEvent,
            EventType.BLUEPRINT_UNINSTALL: BlueprintInstallEvent,
            EventType.ERROR: ErrorEvent,
            EventType.BILLING_USAGE: BillingUsageEvent,
            EventType.TENANT_CREATED: TenantEvent,
            EventType.TENANT_UPDATED: TenantEvent,
            EventType.PROJECT_CREATED: ProjectEvent,
            EventType.PROJECT_UPDATED: ProjectEvent,
            EventType.USER_ACTIVATED: UserActivatedEvent,
            EventType.REFERRAL_SENT: ReferralEvent,
            EventType.REFERRAL_CONVERTED: ReferralEvent,
            EventType.REVENUE: RevenueEvent,
            EventType.USER_SIGNUP: UserSignupEvent,
            EventType.USER_LOGIN: UserLoginEvent,
        }
        
        event_class = event_classes.get(event_type)
        if not event_class:
            return None
        
        # Convert timestamp string back to datetime
        if "timestamp" in event_dict and isinstance(event_dict["timestamp"], str):
            event_dict["timestamp"] = datetime.fromisoformat(event_dict["timestamp"])
        
        # Keep ``event_type`` for the base dataclass constructor.  Concrete
        # events validate/set their canonical type again in ``__post_init__``.
        
        try:
            return event_class(**event_dict)
        except Exception:
            return None
