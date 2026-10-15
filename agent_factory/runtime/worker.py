"""
Worker for processing jobs from the queue.
"""

import threading
import time
from datetime import datetime

from agent_factory.runtime.engine import RuntimeEngine
from agent_factory.runtime.jobs import Job, JobQueue, JobStatus, JobType, get_job_queue
from agent_factory.telemetry.collector import get_collector


class Worker:
    """
    Worker for processing jobs from the queue.
    
    Example:
        >>> worker = Worker(runtime_engine=runtime)
        >>> worker.start()
        >>> # Worker runs in background
        >>> worker.stop()
    """
    
    def __init__(
        self,
        runtime_engine: RuntimeEngine,
        job_queue: JobQueue | None = None,
        poll_interval: float = 1.0,
    ):
        """
        Initialize worker.
        
        Args:
            runtime_engine: Runtime engine for executing jobs
            job_queue: Job queue (defaults to global queue)
            poll_interval: Polling interval in seconds
        """
        self.runtime_engine = runtime_engine
        self.job_queue = job_queue or get_job_queue()
        self.poll_interval = poll_interval
        self.running = False
        self.thread: threading.Thread | None = None
    
    def start(self) -> None:
        """Start worker in background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop worker."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
    
    def _run(self) -> None:
        """Worker main loop."""
        while self.running:
            try:
                # Dequeue job
                job = self.job_queue.dequeue()
                
                if not job:
                    # No jobs available, sleep
                    time.sleep(self.poll_interval)
                    continue
                
                # Process job
                self._process_job(job)
                
            except Exception as e:
                # Log error and continue
                print(f"Worker error: {e}")
                time.sleep(self.poll_interval)
    
    def _process_job(self, job: Job) -> None:
        """
        Process a single job.
        
        Args:
            job: Job to process
        """
        collector = get_collector()
        
        try:
            if job.job_type == JobType.AGENT_RUN:
                # Run agent
                input_text = job.input_data.get("input_text", "")
                session_id = job.input_data.get("session_id")
                context = job.input_data.get("context")
                
                execution_id = self.runtime_engine.run_agent(
                    agent_id=job.resource_id,
                    input_text=input_text,
                    session_id=session_id,
                    context=context,
                )
                
                execution = self.runtime_engine.get_execution(execution_id)
                
                if execution:
                    job.result = {
                        "execution_id": execution_id,
                        "output": execution.result.output if execution.result else None,
                        "status": execution.status,
                        "execution_time": execution.result.execution_time if execution.result else 0.0,
                    }
                    job.status = JobStatus.COMPLETED
                else:
                    job.status = JobStatus.FAILED
                    job.error = "Execution not found"
            
            elif job.job_type == JobType.WORKFLOW_RUN:
                # Run workflow
                context = job.input_data.get("context", {})
                
                execution_id = self.runtime_engine.run_workflow(
                    workflow_id=job.resource_id,
                    context=context,
                )
                
                execution = self.runtime_engine.get_execution(execution_id)
                
                if execution:
                    job.result = {
                        "execution_id": execution_id,
                        "output": execution.result.output if execution.result else None,
                        "status": execution.status,
                        "execution_time": execution.result.execution_time if execution.result else 0.0,
                    }
                    job.status = JobStatus.COMPLETED
                else:
                    job.status = JobStatus.FAILED
                    job.error = "Execution not found"
            
            else:
                job.status = JobStatus.FAILED
                job.error = f"Unknown job type: {job.job_type}"
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            
            # Record error in telemetry
            collector.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                project_id=job.project_id,
                resource_type=job.job_type.value,
                resource_id=job.resource_id,
            )
        
        finally:
            job.completed_at = datetime.utcnow()
            self.job_queue.update_job(job)
            
            # Record telemetry
            if job.job_type == JobType.AGENT_RUN and job.status == JobStatus.COMPLETED:
                collector.record_agent_run(
                    agent_id=job.resource_id,
                    tenant_id=job.tenant_id,
                    user_id=job.user_id,
                    project_id=job.project_id,
                    status="completed" if job.status == JobStatus.COMPLETED else "failed",
                    execution_time=job.result.get("execution_time", 0.0) if job.result else 0.0,
                )
            elif job.job_type == JobType.WORKFLOW_RUN and job.status == JobStatus.COMPLETED:
                collector.record_workflow_run(
                    workflow_id=job.resource_id,
                    tenant_id=job.tenant_id,
                    user_id=job.user_id,
                    project_id=job.project_id,
                    status="completed" if job.status == JobStatus.COMPLETED else "failed",
                    execution_time=job.result.get("execution_time", 0.0) if job.result else 0.0,
                )
