"""Tests for job queue system."""

import pytest

from agent_factory.runtime.jobs import (
    InMemoryJobQueue,
    Job,
    JobStatus,
    JobType,
    SQLiteJobQueue,
    get_job_queue,
)


@pytest.mark.unit
def test_job_creation():
    """Test creating a job."""
    job = Job(
        job_id="job-123",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={"input_text": "Hello"},
    )

    assert job.job_id == "job-123"
    assert job.job_type == JobType.AGENT_RUN
    assert job.status == JobStatus.QUEUED
    assert job.input_data["input_text"] == "Hello"


@pytest.mark.unit
def test_in_memory_queue_enqueue():
    """Test enqueueing a job."""
    queue = InMemoryJobQueue()
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
    )

    queue.enqueue(job)

    assert "job-1" in queue.jobs
    assert queue.jobs["job-1"] == job


@pytest.mark.unit
def test_in_memory_queue_dequeue():
    """Test dequeueing a job."""
    queue = InMemoryJobQueue()
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
    )

    queue.enqueue(job)
    dequeued = queue.dequeue()

    assert dequeued is not None
    assert dequeued.job_id == "job-1"
    assert dequeued.status == JobStatus.RUNNING


@pytest.mark.unit
def test_in_memory_queue_dequeue_empty():
    """Test dequeueing from empty queue."""
    queue = InMemoryJobQueue()
    result = queue.dequeue()

    assert result is None


@pytest.mark.unit
def test_in_memory_queue_get_job():
    """Test getting a job by ID."""
    queue = InMemoryJobQueue()
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
    )

    queue.enqueue(job)
    retrieved = queue.get_job("job-1")

    assert retrieved == job


@pytest.mark.unit
def test_in_memory_queue_update_job():
    """Test updating a job."""
    queue = InMemoryJobQueue()
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
    )

    queue.enqueue(job)
    job.status = JobStatus.COMPLETED
    job.result = {"output": "Done"}
    queue.update_job(job)

    updated = queue.get_job("job-1")
    assert updated.status == JobStatus.COMPLETED
    assert updated.result == {"output": "Done"}


@pytest.mark.unit
def test_in_memory_queue_list_jobs():
    """Test listing jobs."""
    queue = InMemoryJobQueue()

    job1 = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
        tenant_id="tenant-1",
    )
    job2 = Job(
        job_id="job-2",
        job_type=JobType.WORKFLOW_RUN,
        resource_id="workflow-1",
        input_data={},
        tenant_id="tenant-1",
    )

    queue.enqueue(job1)
    queue.enqueue(job2)

    jobs = queue.list_jobs(tenant_id="tenant-1")
    assert len(jobs) == 2


@pytest.mark.unit
def test_sqlite_queue_enqueue_dequeue(tmp_path):
    """Test SQLite queue enqueue and dequeue."""
    db_path = tmp_path / "test_jobs.db"
    queue = SQLiteJobQueue(str(db_path))

    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={"input_text": "Hello"},
    )

    queue.enqueue(job)
    dequeued = queue.dequeue()

    assert dequeued is not None
    assert dequeued.job_id == "job-1"
    assert dequeued.status == JobStatus.RUNNING


@pytest.mark.unit
def test_get_job_queue_singleton():
    """Test get_job_queue returns singleton."""
    queue1 = get_job_queue()
    queue2 = get_job_queue()

    assert queue1 is queue2
