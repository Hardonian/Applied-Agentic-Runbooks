"""Scheduler API routes."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agent_factory.runtime.scheduler import Scheduler
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import Permission, require_permission

router = APIRouter()
scheduler = Scheduler()


class ScheduleAgentRequest(BaseModel):
    """Schedule agent request."""

    agent_id: str
    input_text: str
    schedule_str: str = "daily"


class ScheduleWorkflowRequest(BaseModel):
    """Schedule workflow request."""

    workflow_id: str
    context: dict[str, Any]
    schedule_str: str = "daily"


@router.post("/agent", response_model=dict[str, Any])
async def schedule_agent(request: ScheduleAgentRequest, user=Depends(get_current_user)):
    """Schedule an agent to run on a schedule."""
    require_permission(Permission.WRITE_AGENTS)(lambda: None)()

    from agent_factory.runtime.engine import RuntimeEngine

    runtime = RuntimeEngine()

    def run_func(agent_id: str, input_text: str):
        runtime.run_agent(agent_id, input_text)

    job_id = scheduler.schedule_agent(
        agent_id=request.agent_id,
        input_text=request.input_text,
        schedule_str=request.schedule_str,
        run_func=run_func,
    )

    return {"job_id": job_id, "status": "scheduled"}


@router.post("/workflow", response_model=dict[str, Any])
async def schedule_workflow(request: ScheduleWorkflowRequest, user=Depends(get_current_user)):
    """Schedule a workflow to run on a schedule."""
    require_permission(Permission.WRITE_WORKFLOWS)(lambda: None)()

    from agent_factory.runtime.engine import RuntimeEngine

    runtime = RuntimeEngine()

    def run_func(workflow_id: str, context: dict[str, Any]):
        runtime.run_workflow(workflow_id, context)

    job_id = scheduler.schedule_workflow(
        workflow_id=request.workflow_id,
        context=request.context,
        schedule_str=request.schedule_str,
        run_func=run_func,
    )

    return {"job_id": job_id, "status": "scheduled"}


@router.get("/jobs", response_model=list[str])
def list_scheduled_jobs():
    """List all scheduled jobs."""
    return list(scheduler.jobs.keys())


@router.post("/start")
async def start_scheduler(user=Depends(get_current_user)):
    """Start the scheduler."""
    require_permission(Permission.ADMIN)(lambda: None)()

    scheduler.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_scheduler(user=Depends(get_current_user)):
    """Stop the scheduler."""
    require_permission(Permission.ADMIN)(lambda: None)()

    scheduler.stop()
    return {"status": "stopped"}
