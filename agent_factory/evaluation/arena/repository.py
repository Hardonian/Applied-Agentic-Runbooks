"""Durable tenant-scoped persistence for Arena jobs and summaries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete

from agent_factory.database.models import ArenaRun
from agent_factory.database.session import Base, SessionLocal, engine


class ArenaRepository:
    """Persist Arena lifecycle state using the configured SQLite/PostgreSQL engine."""

    def __init__(self, retention_days: int = 30) -> None:
        self.retention_days = max(1, retention_days)
        Base.metadata.create_all(bind=engine, tables=[ArenaRun.__table__])

    def create(
        self,
        run_id: str,
        request: dict[str, Any],
        *,
        tenant_id: str = "public",
        created_by: str | None = None,
        mode: str = "deterministic",
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        record = ArenaRun(
            id=run_id,
            tenant_id=tenant_id,
            created_by=created_by,
            status="queued",
            mode=mode,
            request=request,
            created_at=now,
            expires_at=now + timedelta(days=self.retention_days),
        )
        with SessionLocal() as session:
            session.add(record)
            session.commit()
        return self.get(run_id, tenant_id) or {}

    def update(self, run_id: str, tenant_id: str = "public", **values: Any) -> dict[str, Any] | None:
        with SessionLocal() as session:
            record = (
                session.query(ArenaRun)
                .filter(ArenaRun.id == run_id, ArenaRun.tenant_id == tenant_id)
                .first()
            )
            if record is None:
                return None
            for key, value in values.items():
                setattr(record, key, value)
            session.commit()
        return self.get(run_id, tenant_id)

    def get(self, run_id: str, tenant_id: str = "public") -> dict[str, Any] | None:
        with SessionLocal() as session:
            record = (
                session.query(ArenaRun)
                .filter(ArenaRun.id == run_id, ArenaRun.tenant_id == tenant_id)
                .first()
            )
            return self._serialize(record) if record else None

    def list(
        self, tenant_id: str = "public", *, limit: int = 50, status: str | None = None
    ) -> list[dict[str, Any]]:
        with SessionLocal() as session:
            query = session.query(ArenaRun).filter(ArenaRun.tenant_id == tenant_id)
            if status:
                query = query.filter(ArenaRun.status == status)
            records = query.order_by(ArenaRun.created_at.desc()).limit(max(1, min(limit, 200))).all()
            return [self._serialize(record) for record in records]

    def request_cancel(self, run_id: str, tenant_id: str = "public") -> bool:
        record = self.get(run_id, tenant_id)
        if not record or record["status"] in {"passed", "failed", "cancelled"}:
            return False
        self.update(run_id, tenant_id, cancel_requested=True)
        return True

    def purge_expired(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with SessionLocal() as session:
            result = session.execute(delete(ArenaRun).where(ArenaRun.expires_at < now))
            session.commit()
            return int(result.rowcount or 0)

    @staticmethod
    def _serialize(record: ArenaRun) -> dict[str, Any]:
        return {
            "run_id": record.id,
            "tenant_id": record.tenant_id,
            "created_by": record.created_by,
            "status": record.status,
            "mode": record.mode,
            "benchmark_version": record.benchmark_version,
            "request": record.request or {},
            "summary": record.summary,
            "error": record.error,
            "cancel_requested": bool(record.cancel_requested),
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        }
