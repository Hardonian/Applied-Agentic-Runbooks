"""Scheduler API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agent_factory.api.runtime import runtime
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.scheduler import Scheduler
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import Permission, require_user_permission

router = APIRouter()
scheduler = Scheduler()
registry = LocalRegistry()


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
async def schedule_agent(
    request: ScheduleAgentRequest,
    user=Depends(get_current_user)
):
    """Schedule an agent to run on a schedule."""
    require_user_permission(user, Permission.WRITE_AGENTS)
    agent = registry.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    runtime.register_agent(agent)
    
    def run_func(agent_id: str, input_text: str):
        runtime.run_agent(agent_id, input_text)
    
    job_id = scheduler.schedule_agent(
        agent_id=request.agent_id,
        input_text=request.input_text,
        schedule_str=request.schedule_str,
        run_func=run_func
    )
    
    return {"job_id": job_id, "status": "scheduled"}


@router.post("/workflow", response_model=dict[str, Any])
async def schedule_workflow(
    request: ScheduleWorkflowRequest,
    user=Depends(get_current_user)
):
    """Schedule a workflow to run on a schedule."""
    require_user_permission(user, Permission.WRITE_WORKFLOWS)
    workflow = registry.get_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    runtime.register_workflow(workflow)
    
    def run_func(workflow_id: str, context: dict[str, Any]):
        runtime.run_workflow(workflow_id, context)
    
    job_id = scheduler.schedule_workflow(
        workflow_id=request.workflow_id,
        context=request.context,
        schedule_str=request.schedule_str,
        run_func=run_func
    )
    
    return {"job_id": job_id, "status": "scheduled"}


@router.get("/jobs", response_model=list[str])
def list_scheduled_jobs(user=Depends(get_current_user)):
    """List all scheduled jobs."""
    require_user_permission(user, Permission.READ_WORKFLOWS)
    return list(scheduler.jobs.keys())


@router.delete("/jobs/{job_id}", response_model=dict[str, Any])
def cancel_scheduled_job(job_id: str, user=Depends(get_current_user)):
    """Cancel a scheduled job without stopping the scheduler service."""
    require_user_permission(user, Permission.ADMIN)
    if not scheduler.cancel(job_id):
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return {"job_id": job_id, "status": "cancelled"}


@router.post("/start")
async def start_scheduler(user=Depends(get_current_user)):
    """Start the scheduler."""
    require_user_permission(user, Permission.ADMIN)
    
    scheduler.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_scheduler(user=Depends(get_current_user)):
    """Stop the scheduler."""
    require_user_permission(user, Permission.ADMIN)
    
    scheduler.stop()
    return {"status": "stopped"}
