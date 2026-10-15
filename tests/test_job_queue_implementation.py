"""
Tests for job queue implementation.
"""

from agent_factory.jobs.queue import (
    InMemoryJobQueue,
    Job,
    JobStatus,
    JobWorker,
    get_job_queue,
)


def test_in_memory_queue_enqueue():
    """Test in-memory queue enqueue."""
    queue = InMemoryJobQueue()
    
    job = Job(
        id="test-job",
        job_type="test",
        payload={"test": "data"},
    )
    
    job_id = queue.enqueue(job)
    assert job_id == "test-job"
    assert job.status == JobStatus.QUEUED


def test_in_memory_queue_dequeue():
    """Test in-memory queue dequeue."""
    queue = InMemoryJobQueue()
    
    job = Job(
        id="test-job",
        job_type="test",
        payload={"test": "data"},
    )
    
    queue.enqueue(job)
    dequeued = queue.dequeue()
    
    assert dequeued is not None
    assert dequeued.id == "test-job"
    assert dequeued.status == JobStatus.RUNNING


def test_in_memory_queue_priority():
    """Test in-memory queue priority ordering."""
    queue = InMemoryJobQueue()
    
    job1 = Job(id="job1", job_type="test", payload={}, priority=1)
    job2 = Job(id="job2", job_type="test", payload={}, priority=5)
    job3 = Job(id="job3", job_type="test", payload={}, priority=3)
    
    queue.enqueue(job1)
    queue.enqueue(job2)
    queue.enqueue(job3)
    
    # Highest priority should be dequeued first
    dequeued = queue.dequeue()
    assert dequeued.id == "job2"  # Priority 5


def test_in_memory_queue_get_job():
    """Test in-memory queue get job."""
    queue = InMemoryJobQueue()
    
    job = Job(id="test-job", job_type="test", payload={})
    queue.enqueue(job)
    
    retrieved = queue.get_job("test-job")
    assert retrieved is not None
    assert retrieved.id == "test-job"


def test_in_memory_queue_update_job():
    """Test in-memory queue update job."""
    queue = InMemoryJobQueue()
    
    job = Job(id="test-job", job_type="test", payload={})
    queue.enqueue(job)
    
    job.status = JobStatus.COMPLETED
    queue.update_job(job)
    
    updated = queue.get_job("test-job")
    assert updated.status == JobStatus.COMPLETED


def test_in_memory_queue_cancel_job():
    """Test in-memory queue cancel job."""
    queue = InMemoryJobQueue()
    
    job = Job(id="test-job", job_type="test", payload={})
    queue.enqueue(job)
    
    cancelled = queue.cancel_job("test-job")
    assert cancelled is True
    
    retrieved = queue.get_job("test-job")
    assert retrieved.status == JobStatus.CANCELLED


def test_job_worker_process():
    """Test job worker processing."""
    queue = InMemoryJobQueue()
    
    results = []
    
    def handler(payload):
        results.append(payload)
        return "success"
    
    handlers = {"test": handler}
    worker = JobWorker(queue, handlers)
    
    job = Job(id="test-job", job_type="test", payload={"test": "data"})
    queue.enqueue(job)
    
    # Process job manually
    worker._process_job(queue.dequeue())
    
    assert len(results) == 1
    assert results[0]["test"] == "data"


def test_get_job_queue_memory():
    """Test get job queue memory."""
    queue = get_job_queue("memory")
    assert isinstance(queue, InMemoryJobQueue)
