"""
Job queue system for async execution of agents and workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Job status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type."""
    AGENT_RUN = "agent_run"
    WORKFLOW_RUN = "workflow_run"


@dataclass
class Job:
    """
    Job for async execution.
    
    Example:
        >>> job = Job(
        ...     job_id="job-123",
        ...     job_type=JobType.AGENT_RUN,
        ...     resource_id="agent-456",
        ...     input_data={"input_text": "Hello"},
        ...     tenant_id="tenant-789",
        ... )
    """
    job_id: str
    job_type: JobType
    resource_id: str  # agent_id or workflow_id
    input_data: dict[str, Any]
    tenant_id: str | None = None
    user_id: str | None = None
    project_id: str | None = None
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


class JobQueue(ABC):
    """
    Abstract job queue interface.
    
    Implementations can use in-memory, SQLite, Redis, SQS, etc.
    """
    
    @abstractmethod
    def enqueue(self, job: Job) -> None:
        """
        Enqueue a job.
        
        Args:
            job: Job to enqueue
        """
    
    @abstractmethod
    def dequeue(self, job_type: JobType | None = None) -> Job | None:
        """
        Dequeue a job.
        
        Args:
            job_type: Optional job type filter
            
        Returns:
            Job or None if queue is empty
        """
    
    @abstractmethod
    def get_job(self, job_id: str) -> Job | None:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None
        """
    
    @abstractmethod
    def update_job(self, job: Job) -> None:
        """
        Update job status.
        
        Args:
            job: Job to update
        """
    
    @abstractmethod
    def list_jobs(
        self,
        tenant_id: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """
        List jobs with filters.
        
        Args:
            tenant_id: Optional tenant ID filter
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of jobs
        """


class InMemoryJobQueue(JobQueue):
    """
    In-memory job queue (for development/testing).
    
    Not suitable for production with multiple workers.
    """
    
    def __init__(self):
        """Initialize in-memory queue."""
        self.jobs: dict[str, Job] = {}
        self.queue: list[str] = []  # List of job IDs in queue order
    
    def enqueue(self, job: Job) -> None:
        """Enqueue a job."""
        self.jobs[job.job_id] = job
        if job.status == JobStatus.QUEUED:
            self.queue.append(job.job_id)
    
    def dequeue(self, job_type: JobType | None = None) -> Job | None:
        """Dequeue a job."""
        while self.queue:
            job_id = self.queue.pop(0)
            job = self.jobs.get(job_id)
            
            if not job:
                continue
            
            if job_type and job.job_type != job_type:
                # Put back at end if wrong type
                self.queue.append(job_id)
                continue
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            return job
        
        return None
    
    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def update_job(self, job: Job) -> None:
        """Update job."""
        self.jobs[job.job_id] = job
        
        # Remove from queue if completed/failed/cancelled
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            if job.job_id in self.queue:
                self.queue.remove(job.job_id)
    
    def list_jobs(
        self,
        tenant_id: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs."""
        jobs = list(self.jobs.values())
        
        if tenant_id:
            jobs = [j for j in jobs if j.tenant_id == tenant_id]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]


class SQLiteJobQueue(JobQueue):
    """
    SQLite-based job queue (for single-worker deployments).
    """
    
    def __init__(self, db_path: str = "./agent_factory/jobs.db"):
        """
        Initialize SQLite job queue.
        
        Args:
            db_path: Path to SQLite database
        """
        from pathlib import Path
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                input_data TEXT NOT NULL,
                tenant_id TEXT,
                user_id TEXT,
                project_id TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status 
            ON jobs(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_tenant 
            ON jobs(tenant_id)
        """)
        
        conn.commit()
        conn.close()
    
    def enqueue(self, job: Job) -> None:
        """Enqueue a job."""
        import json
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO jobs 
                (job_id, job_type, resource_id, input_data, tenant_id, user_id, project_id,
                 status, created_at, started_at, completed_at, result, error, retry_count,
                 max_retries, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.job_type.value,
                job.resource_id,
                json.dumps(job.input_data),
                job.tenant_id,
                job.user_id,
                job.project_id,
                job.status.value,
                job.created_at.isoformat(),
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                json.dumps(job.result) if job.result else None,
                job.error,
                job.retry_count,
                job.max_retries,
                json.dumps(job.metadata),
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def dequeue(self, job_type: JobType | None = None) -> Job | None:
        """Dequeue a job."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT * FROM jobs 
                WHERE status = ? 
                ORDER BY created_at ASC 
                LIMIT 1
            """
            
            cursor.execute(query, (JobStatus.QUEUED.value,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Parse row
            job = self._row_to_job(row)
            
            if job_type and job.job_type != job_type:
                return None
            
            # Update status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.update_job(job)
            
            return job
        finally:
            conn.close()
    
    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_job(row)
        finally:
            conn.close()
    
    def update_job(self, job: Job) -> None:
        """Update job."""
        self.enqueue(job)  # Same logic as enqueue
    
    def list_jobs(
        self,
        tenant_id: str | None = None,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []
            
            if tenant_id:
                query += " AND tenant_id = ?"
                params.append(tenant_id)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_job(row) for row in rows]
        finally:
            conn.close()
    
    def _row_to_job(self, row: tuple) -> Job:
        """Convert database row to Job."""
        import json
        
        return Job(
            job_id=row[0],
            job_type=JobType(row[1]),
            resource_id=row[2],
            input_data=json.loads(row[3]),
            tenant_id=row[4],
            user_id=row[5],
            project_id=row[6],
            status=JobStatus(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            started_at=datetime.fromisoformat(row[9]) if row[9] else None,
            completed_at=datetime.fromisoformat(row[10]) if row[10] else None,
            result=json.loads(row[11]) if row[11] else None,
            error=row[12],
            retry_count=row[13],
            max_retries=row[14],
            metadata=json.loads(row[15]) if row[15] else {},
        )


# Global job queue instance
_job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    """
    Get global job queue instance.
    
    Returns:
        Job queue
    """
    global _job_queue
    if _job_queue is None:
        # Use SQLite by default
        _job_queue = SQLiteJobQueue()
    return _job_queue
