"""
Job queue implementation for background task processing.
"""

import json
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import threading
import time


class JobStatus(str, Enum):
    """Job status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job definition."""
    id: str
    job_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    priority: int = 0  # Higher priority runs first
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class JobQueue(ABC):
    """Abstract job queue interface."""
    
    @abstractmethod
    def enqueue(self, job: Job) -> str:
        """Add job to queue."""
        pass
    
    @abstractmethod
    def dequeue(self, job_type: Optional[str] = None) -> Optional[Job]:
        """Get next job from queue."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        pass
    
    @abstractmethod
    def update_job(self, job: Job) -> None:
        """Update job status."""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        pass


class InMemoryJobQueue(JobQueue):
    """In-memory job queue implementation."""
    
    def __init__(self):
        """Initialize in-memory job queue."""
        self.jobs: Dict[str, Job] = {}
        self.queue: List[str] = []  # Job IDs in priority order
        self.lock = threading.Lock()
    
    def enqueue(self, job: Job) -> str:
        """Add job to queue."""
        with self.lock:
            self.jobs[job.id] = job
            job.status = JobStatus.QUEUED
            
            # Insert in priority order
            inserted = False
            for i, queued_id in enumerate(self.queue):
                queued_job = self.jobs[queued_id]
                if job.priority > queued_job.priority:
                    self.queue.insert(i, job.id)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(job.id)
            
            return job.id
    
    def dequeue(self, job_type: Optional[str] = None) -> Optional[Job]:
        """Get next job from queue."""
        with self.lock:
            for job_id in self.queue:
                job = self.jobs.get(job_id)
                if job and job.status == JobStatus.QUEUED:
                    if job_type is None or job.job_type == job_type:
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.now()
                        self.queue.remove(job_id)
                        return job
            return None
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job(self, job: Job) -> None:
        """Update job status."""
        with self.lock:
            self.jobs[job.id] = job
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
                job.status = JobStatus.CANCELLED
                if job_id in self.queue:
                    self.queue.remove(job_id)
                return True
            return False


class RedisJobQueue(JobQueue):
    """Redis-based job queue implementation."""
    
    def __init__(self, redis_client=None, key_prefix: str = "job_queue:"):
        """
        Initialize Redis job queue.
        
        Args:
            redis_client: Redis client instance
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
                raise ImportError("redis package is required for RedisJobQueue")
            except Exception as e:
                raise ValueError(f"Failed to connect to Redis: {e}")
    
    def _get_job_key(self, job_id: str) -> str:
        """Get Redis key for job."""
        return f"{self.key_prefix}job:{job_id}"
    
    def _get_queue_key(self, job_type: Optional[str] = None) -> str:
        """Get Redis key for queue."""
        if job_type:
            return f"{self.key_prefix}queue:{job_type}"
        return f"{self.key_prefix}queue:default"
    
    def enqueue(self, job: Job) -> str:
        """Add job to queue."""
        job.status = JobStatus.QUEUED
        job_key = self._get_job_key(job.id)
        queue_key = self._get_queue_key(job.job_type)
        
        # Store job data
        job_data = json.dumps({
            "id": job.id,
            "job_type": job.job_type,
            "payload": job.payload,
            "status": job.status.value,
            "priority": job.priority,
            "created_at": job.created_at.isoformat(),
            "max_retries": job.max_retries,
            "metadata": job.metadata,
        })
        
        self.redis.set(job_key, job_data)
        
        # Add to queue (sorted set by priority)
        self.redis.zadd(queue_key, {job.id: -job.priority})  # Negative for descending order
        
        return job.id
    
    def dequeue(self, job_type: Optional[str] = None) -> Optional[Job]:
        """Get next job from queue."""
        queue_key = self._get_queue_key(job_type)
        
        # Get highest priority job
        job_ids = self.redis.zrevrange(queue_key, 0, 0)
        
        if not job_ids:
            return None
        
        job_id = job_ids[0]
        job_key = self._get_job_key(job_id)
        
        # Get job data
        job_data = self.redis.get(job_key)
        if not job_data:
            # Clean up orphaned queue entry
            self.redis.zrem(queue_key, job_id)
            return None
        
        data = json.loads(job_data)
        
        # Update status
        data["status"] = JobStatus.RUNNING.value
        data["started_at"] = datetime.now().isoformat()
        self.redis.set(job_key, json.dumps(data))
        
        # Remove from queue
        self.redis.zrem(queue_key, job_id)
        
        # Reconstruct job
        job = Job(
            id=data["id"],
            job_type=data["job_type"],
            payload=data["payload"],
            status=JobStatus(data["status"]),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )
        
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        job_key = self._get_job_key(job_id)
        job_data = self.redis.get(job_key)
        
        if not job_data:
            return None
        
        data = json.loads(job_data)
        
        return Job(
            id=data["id"],
            job_type=data["job_type"],
            payload=data["payload"],
            status=JobStatus(data["status"]),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data.get("started_at")) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data.get("completed_at")) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )
    
    def update_job(self, job: Job) -> None:
        """Update job status."""
        job_key = self._get_job_key(job.id)
        
        job_data = {
            "id": job.id,
            "job_type": job.job_type,
            "payload": job.payload,
            "status": job.status.value,
            "priority": job.priority,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "metadata": job.metadata,
        }
        
        self.redis.set(job_key, json.dumps(job_data))
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.get_job(job_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
            job.status = JobStatus.CANCELLED
            self.update_job(job)
            
            # Remove from queue
            queue_key = self._get_queue_key(job.job_type)
            self.redis.zrem(queue_key, job_id)
            
            return True
        return False


class JobWorker:
    """Worker for processing jobs."""
    
    def __init__(self, queue: JobQueue, handlers: Dict[str, Callable]):
        """
        Initialize job worker.
        
        Args:
            queue: Job queue instance
            handlers: Dictionary mapping job types to handler functions
        """
        self.queue = queue
        self.handlers = handlers
        self.running = False
        self.thread = None
    
    def start(self) -> None:
        """Start worker thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop worker thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _worker_loop(self) -> None:
        """Main worker loop."""
        while self.running:
            try:
                # Try to get a job
                job = self.queue.dequeue()
                
                if job:
                    self._process_job(job)
                else:
                    # No jobs available, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                import logging
                logging.error(f"Error in worker loop: {e}")
                time.sleep(1)
    
    def _process_job(self, job: Job) -> None:
        """Process a single job."""
        handler = self.handlers.get(job.job_type)
        
        if not handler:
            job.status = JobStatus.FAILED
            job.error = f"No handler for job type: {job.job_type}"
            job.completed_at = datetime.now()
            self.queue.update_job(job)
            return
        
        try:
            # Execute handler
            result = handler(job.payload)
            
            # Mark as completed
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now()
            self.queue.update_job(job)
            
        except Exception as e:
            # Handle failure
            job.retry_count += 1
            
            if job.retry_count < job.max_retries:
                # Retry
                job.status = JobStatus.QUEUED
                job.error = None
                self.queue.enqueue(job)
            else:
                # Max retries reached
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.now()
                self.queue.update_job(job)


def get_job_queue(queue_type: str = "memory", **kwargs) -> JobQueue:
    """
    Get job queue instance.
    
    Args:
        queue_type: Type of queue ("memory" or "redis")
        **kwargs: Additional arguments
        
    Returns:
        JobQueue instance
    """
    if queue_type == "memory":
        return InMemoryJobQueue()
    elif queue_type == "redis":
        redis_client = kwargs.get("redis_client")
        key_prefix = kwargs.get("key_prefix", "job_queue:")
        return RedisJobQueue(redis_client=redis_client, key_prefix=key_prefix)
    else:
        raise ValueError(f"Unknown queue type: {queue_type}")
