"""Tests for worker system."""

import time
from unittest.mock import Mock, patch

import pytest

from agent_factory.runtime.engine import RuntimeEngine
from agent_factory.runtime.jobs import InMemoryJobQueue, Job, JobStatus, JobType
from agent_factory.runtime.worker import Worker


@pytest.mark.unit
def test_worker_initialization():
    """Test worker initialization."""
    runtime = Mock(spec=RuntimeEngine)
    queue = InMemoryJobQueue()
    
    worker = Worker(
        runtime_engine=runtime,
        job_queue=queue,
        poll_interval=0.1,
    )
    
    assert worker.runtime_engine == runtime
    assert worker.job_queue == queue
    assert worker.poll_interval == 0.1
    assert worker.running is False


@pytest.mark.unit
def test_worker_start_stop():
    """Test starting and stopping worker."""
    runtime = Mock(spec=RuntimeEngine)
    queue = InMemoryJobQueue()
    
    worker = Worker(
        runtime_engine=runtime,
        job_queue=queue,
        poll_interval=0.1,
    )
    
    worker.start()
    assert worker.running is True
    assert worker.thread is not None
    
    # Give it a moment to start
    time.sleep(0.1)
    
    worker.stop()
    assert worker.running is False


@pytest.mark.unit
@patch('agent_factory.runtime.worker.get_collector')
def test_worker_process_agent_job(mock_get_collector):
    """Test worker processing an agent job."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector
    
    runtime = Mock(spec=RuntimeEngine)
    runtime.run_agent.return_value = "exec-123"
    
    execution = Mock()
    execution.result = Mock()
    execution.result.output = "Hello"
    execution.result.execution_time = 1.5
    execution.status = "completed"
    
    runtime.get_execution.return_value = execution
    
    queue = InMemoryJobQueue()
    worker = Worker(runtime_engine=runtime, job_queue=queue)
    
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={"input_text": "Hello"},
    )
    
    queue.enqueue(job)
    worker._process_job(job)
    
    assert job.status == JobStatus.COMPLETED
    assert job.result is not None
    assert job.result["execution_id"] == "exec-123"


@pytest.mark.unit
@patch('agent_factory.runtime.worker.get_collector')
def test_worker_process_workflow_job(mock_get_collector):
    """Test worker processing a workflow job."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector
    
    runtime = Mock(spec=RuntimeEngine)
    runtime.run_workflow.return_value = "exec-456"
    
    execution = Mock()
    execution.result = Mock()
    execution.result.output = {"step1": "done"}
    execution.result.execution_time = 2.0
    execution.status = "completed"
    
    runtime.get_execution.return_value = execution
    
    queue = InMemoryJobQueue()
    worker = Worker(runtime_engine=runtime, job_queue=queue)
    
    job = Job(
        job_id="job-2",
        job_type=JobType.WORKFLOW_RUN,
        resource_id="workflow-1",
        input_data={"context": {}},
    )
    
    queue.enqueue(job)
    worker._process_job(job)
    
    assert job.status == JobStatus.COMPLETED
    assert job.result["execution_id"] == "exec-456"


@pytest.mark.unit
@patch('agent_factory.runtime.worker.get_collector')
def test_worker_process_job_error(mock_get_collector):
    """Test worker handling job errors."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector
    
    runtime = Mock(spec=RuntimeEngine)
    runtime.run_agent.side_effect = Exception("Test error")
    
    queue = InMemoryJobQueue()
    worker = Worker(runtime_engine=runtime, job_queue=queue)
    
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={"input_text": "Hello"},
    )
    
    worker._process_job(job)
    
    assert job.status == JobStatus.FAILED
    assert job.error == "Test error"
    assert mock_collector.record_error.called


@pytest.mark.unit
@patch('agent_factory.runtime.worker.get_collector')
def test_worker_unknown_job_type(mock_get_collector):
    """Test worker handling unknown job type."""
    mock_collector = Mock()
    mock_get_collector.return_value = mock_collector
    
    runtime = Mock(spec=RuntimeEngine)
    queue = InMemoryJobQueue()
    worker = Worker(runtime_engine=runtime, job_queue=queue)
    
    # Create job with valid type, then modify to invalid
    job = Job(
        job_id="job-1",
        job_type=JobType.AGENT_RUN,
        resource_id="agent-1",
        input_data={},
    )
    # Simulate invalid job type by checking what happens with wrong type
    # The worker checks job.job_type against JobType enum values
    # If it doesn't match, it will fail
    job.job_type = Mock()  # Mock object that won't match JobType enum
    
    worker._process_job(job)
    
    assert job.status == JobStatus.FAILED
    assert job.error is not None
