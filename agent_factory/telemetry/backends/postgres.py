"""
PostgreSQL backend for telemetry storage.
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from agent_factory.telemetry.backends.base import TelemetryBackend
from agent_factory.telemetry.model import EventType, TelemetryEvent

Base = declarative_base()


class TelemetryEventModel(Base):
    """SQLAlchemy model for telemetry events."""
    __tablename__ = "telemetry_events"
    
    event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    project_id = Column(String)
    event_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_telemetry_tenant_type", "tenant_id", "event_type"),
        Index("idx_telemetry_timestamp_type", "timestamp", "event_type"),
    )


class PostgresTelemetryBackend(TelemetryBackend):
    """
    PostgreSQL storage backend for telemetry events.
    
    Suitable for production deployments with high volume.
    """
    
    def __init__(self, database_url: str | None = None):
        """
        Initialize PostgreSQL telemetry backend.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        import os
        
        if not database_url:
            database_url = os.getenv(
                "TELEMETRY_DATABASE_URL",
                os.getenv("DATABASE_URL", "postgresql://localhost/agent_factory")
            )
        
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
    
    def store_event(self, event: TelemetryEvent) -> None:
        """Store a telemetry event."""
        session = self.SessionLocal()
        
        try:
            event_data = json.dumps(event.to_dict())
            
            event_model = TelemetryEventModel(
                event_id=event.event_id,
                event_type=event.event_type.value,
                timestamp=event.timestamp,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                project_id=event.project_id,
                event_data=event_data,
            )
            
            session.add(event_model)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def query_events(
        self,
        event_type: str | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[TelemetryEvent]:
        """Query telemetry events."""
        session = self.SessionLocal()
        
        try:
            query = session.query(TelemetryEventModel)
            
            if event_type:
                query = query.filter(TelemetryEventModel.event_type == event_type)
            
            if tenant_id:
                query = query.filter(TelemetryEventModel.tenant_id == tenant_id)
            
            if user_id:
                query = query.filter(TelemetryEventModel.user_id == user_id)
            
            if project_id:
                query = query.filter(TelemetryEventModel.project_id == project_id)
            
            if start_time:
                query = query.filter(TelemetryEventModel.timestamp >= start_time)
            
            if end_time:
                query = query.filter(TelemetryEventModel.timestamp <= end_time)
            
            query = query.order_by(TelemetryEventModel.timestamp.desc()).limit(limit)
            
            rows = query.all()
            
            events = []
            for row in rows:
                event_dict = json.loads(str(row.event_data or "{}"))
                event = self._deserialize_event(event_dict)
                if event:
                    events.append(event)
            
            return events
        finally:
            session.close()
    
    def _deserialize_event(self, event_dict: dict) -> TelemetryEvent | None:
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
            BillingUsageEvent,
            BlueprintInstallEvent,
            ErrorEvent,
            ProjectEvent,
            ReferralEvent,
            RevenueEvent,
            TenantEvent,
            UserActivatedEvent,
            UserLoginEvent,
            UserSignupEvent,
            WorkflowRunEvent,
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
        
        # Convert timestamp string back to datetime if needed
        if "timestamp" in event_dict and isinstance(event_dict["timestamp"], str):
            event_dict["timestamp"] = datetime.fromisoformat(event_dict["timestamp"])
        
        # Keep ``event_type`` because the base telemetry dataclass requires
        # it; the concrete class also normalizes it in ``__post_init__``.
        
        try:
            return event_class(**event_dict)
        except Exception:
            return None
