"""Workflow API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from agent_factory.workflows.model import Workflow, WorkflowStep, Trigger, TriggerType, Condition
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.api.runtime import runtime
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import require_user_permission, Permission

router = APIRouter()
registry = LocalRegistry()


class WorkflowCreate(BaseModel):
    """Workflow creation model."""
    id: str
    name: str
    steps: List[Dict[str, Any]]
    triggers: Optional[List[Dict[str, Any]]] = None
    branching: Optional[Dict[str, Dict[str, str]]] = None


class WorkflowUpdate(BaseModel):
    """Workflow update model."""
    name: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    branching: Optional[Dict[str, Dict[str, str]]] = None


class WorkflowRun(BaseModel):
    """Workflow run model."""
    context: Dict[str, Any]
    start_step: Optional[str] = None


class WorkflowTrigger(BaseModel):
    """Workflow trigger model."""
    trigger_type: str
    config: Dict[str, Any]


@router.post("/", response_model=Dict[str, Any])
async def create_workflow(
    workflow_data: WorkflowCreate,
    user=Depends(get_current_user)
):
    """Create a new workflow."""
    require_user_permission(user, Permission.WRITE_WORKFLOWS)
    
    # Check if workflow already exists
    existing = registry.get_workflow(workflow_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Workflow {workflow_data.id} already exists")
    
    # Convert steps
    steps = []
    for step_data in workflow_data.steps:
        condition = None
        if step_data.get("condition"):
            cond_data = step_data["condition"]
            condition = Condition(
                expression=cond_data.get("expression", ""),
                description=cond_data.get("description"),
            )
        
        step = WorkflowStep(
            id=step_data["id"],
            agent_id=step_data["agent_id"],
            input_mapping=step_data.get("input_mapping", {}),
            output_mapping=step_data.get("output_mapping", {}),
            condition=condition,
            timeout=step_data.get("timeout", 30),
            retry_attempts=step_data.get("retry_attempts", 3),
        )
        steps.append(step)
    
    # Convert triggers
    triggers = []
    if workflow_data.triggers:
        for trigger_data in workflow_data.triggers:
            trigger = Trigger(
                type=TriggerType(trigger_data.get("type", "manual")),
                config=trigger_data.get("config", {}),
                enabled=trigger_data.get("enabled", True),
            )
            triggers.append(trigger)
    
    # Convert branching
    branching = {}
    if workflow_data.branching:
        for step_id, cond_data in workflow_data.branching.items():
            branching[step_id] = Condition(
                expression=cond_data.get("expression", ""),
                description=cond_data.get("description"),
            )
    
    workflow = Workflow(
        id=workflow_data.id,
        name=workflow_data.name,
        steps=steps,
        triggers=triggers if triggers else None,
        branching=branching if branching else None,
    )
    
    registry.register_workflow(workflow)
    runtime.register_workflow(workflow)
    
    return {"id": workflow.id, "status": "created"}


@router.get("/", response_model=List[str])
def list_workflows():
    """List all workflows."""
    return registry.list_workflows()


@router.get("/{workflow_id}", response_model=Dict[str, Any])
def get_workflow(workflow_id: str):
    """Get workflow by ID."""
    workflow = registry.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow.to_dict()


@router.put("/{workflow_id}", response_model=Dict[str, Any])
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    user=Depends(get_current_user)
):
    """Update a workflow."""
    require_user_permission(user, Permission.WRITE_WORKFLOWS)
    
    workflow = registry.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update fields
    if workflow_data.name:
        workflow.name = workflow_data.name
    
    if workflow_data.steps:
        steps = []
        for step_data in workflow_data.steps:
            condition = None
            if step_data.get("condition"):
                cond_data = step_data["condition"]
                condition = Condition(
                    expression=cond_data.get("expression", ""),
                    description=cond_data.get("description"),
                )
            
            step = WorkflowStep(
                id=step_data["id"],
                agent_id=step_data["agent_id"],
                input_mapping=step_data.get("input_mapping", {}),
                output_mapping=step_data.get("output_mapping", {}),
                condition=condition,
                timeout=step_data.get("timeout", 30),
                retry_attempts=step_data.get("retry_attempts", 3),
            )
            steps.append(step)
        workflow.steps = steps
    
    if workflow_data.triggers is not None:
        triggers = []
        for trigger_data in workflow_data.triggers:
            trigger = Trigger(
                type=TriggerType(trigger_data.get("type", "manual")),
                config=trigger_data.get("config", {}),
                enabled=trigger_data.get("enabled", True),
            )
            triggers.append(trigger)
        workflow.triggers = triggers
    
    if workflow_data.branching is not None:
        branching = {}
        for step_id, cond_data in workflow_data.branching.items():
            branching[step_id] = Condition(
                expression=cond_data.get("expression", ""),
                description=cond_data.get("description"),
            )
        workflow.branching = branching
    
    registry.register_workflow(workflow)
    runtime.register_workflow(workflow)
    
    return {"id": workflow.id, "status": "updated"}


@router.post("/{workflow_id}/run", response_model=Dict[str, Any])
def run_workflow(
    workflow_id: str,
    run_data: WorkflowRun,
    user=Depends(get_current_user),
):
    """Run a workflow."""
    require_user_permission(user, Permission.EXECUTE_WORKFLOWS)
    workflow = registry.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    runtime.register_workflow(workflow)
    try:
        execution_id = runtime.run_workflow(
            workflow_id,
            run_data.context,
            start_step=run_data.start_step,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    
    return {"execution_id": execution_id, "status": "running"}


@router.post("/{workflow_id}/trigger", response_model=Dict[str, Any])
async def trigger_workflow(
    workflow_id: str,
    trigger_data: WorkflowTrigger,
    user=Depends(get_current_user)
):
    """Trigger a workflow manually."""
    require_user_permission(user, Permission.EXECUTE_WORKFLOWS)
    
    workflow = registry.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create context from trigger config
    context = trigger_data.config.copy()
    
    runtime.register_workflow(workflow)
    execution_id = runtime.run_workflow(workflow_id, context)
    
    return {"execution_id": execution_id, "status": "triggered"}


@router.get("/{workflow_id}/status", response_model=Dict[str, Any])
def get_workflow_status(workflow_id: str):
    """Get workflow execution status."""
    workflow = registry.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get recent executions for this workflow
    executions = runtime.list_executions(entity_id=workflow_id, limit=10)
    
    return {
        "workflow_id": workflow_id,
        "recent_executions": [
            {
                "id": ex.id,
                "status": ex.status,
                "created_at": ex.created_at.isoformat(),
                "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
            }
            for ex in executions
        ],
    }


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user=Depends(get_current_user)
):
    """Delete a workflow."""
    require_user_permission(user, Permission.DELETE_WORKFLOWS)
    
    workflow_file = registry.base_path / "workflows" / f"{workflow_id}.json"
    if not workflow_file.exists():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_file.unlink()
    
    # Remove from runtime if registered
    if workflow_id in runtime.workflows_registry:
        del runtime.workflows_registry[workflow_id]
    
    return {"status": "deleted"}
