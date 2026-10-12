"""Execution API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any

from agent_factory.api.runtime import runtime
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import require_user_permission, Permission

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
def list_executions(
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    user=Depends(get_current_user)
):
    """List executions with optional filters."""
    require_user_permission(user, Permission.READ_AGENTS)
    
    executions = runtime.list_executions(
        entity_id=entity_id,
        status=status,
        limit=limit
    )
    
    return [
        {
            "id": ex.id,
            "type": ex.type,
            "entity_id": ex.entity_id,
            "status": ex.status,
            "created_at": ex.created_at.isoformat(),
            "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
            "error": ex.error,
            "metadata": ex.metadata or {},
        }
        for ex in executions
    ]


@router.get("/{execution_id}", response_model=Dict[str, Any])
def get_execution(execution_id: str):
    """Get execution by ID."""
    execution = runtime.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "id": execution.id,
        "type": execution.type,
        "entity_id": execution.entity_id,
        "status": execution.status,
        "created_at": execution.created_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "error": execution.error,
        "metadata": execution.metadata or {},
        "result": execution.result if execution.result else None,
    }


@router.get("/{execution_id}/logs", response_model=Dict[str, Any])
def get_execution_logs(execution_id: str):
    """Get execution logs."""
    execution = runtime.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # In production, logs would be stored separately
    # For now, return execution metadata as logs
    logs = []
    if execution.metadata and "logs" in execution.metadata:
        logs = execution.metadata["logs"]
    elif execution.error:
        logs = [{"level": "error", "message": execution.error, "timestamp": execution.completed_at.isoformat() if execution.completed_at else execution.created_at.isoformat()}]
    
    return {
        "execution_id": execution_id,
        "logs": logs,
    }


@router.post("/{execution_id}/retry", response_model=Dict[str, Any])
async def retry_execution(
    execution_id: str,
    user=Depends(get_current_user)
):
    """Retry a failed execution."""
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    
    execution = runtime.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "error":
        raise HTTPException(status_code=400, detail="Can only retry failed executions")
    
    # Retry execution based on type
    if execution.type == "agent":
        # Get agent and retry
        from agent_factory.registry.local_registry import LocalRegistry
        reg = LocalRegistry()
        agent = reg.get_agent(execution.entity_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        runtime.register_agent(agent)
        
        # Get original input from metadata
        original_input = execution.metadata.get("input_text", "") if execution.metadata else ""
        session_id = execution.metadata.get("session_id") if execution.metadata else None
        
        new_execution_id = runtime.run_agent(
            execution.entity_id,
            original_input,
            session_id=session_id,
        )
    elif execution.type == "workflow":
        # Get workflow and retry
        from agent_factory.registry.local_registry import LocalRegistry
        reg = LocalRegistry()
        workflow = reg.get_workflow(execution.entity_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        runtime.register_workflow(workflow)
        
        # Get original context from metadata
        original_context = execution.metadata.get("context", {}) if execution.metadata else {}
        
        new_execution_id = runtime.run_workflow(
            execution.entity_id,
            original_context,
            start_step=execution.metadata.get("start_step") if execution.metadata else None,
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown execution type")
    
    return {"execution_id": new_execution_id, "status": "retrying"}


@router.delete("/{execution_id}")
async def cancel_execution(
    execution_id: str,
    user=Depends(get_current_user)
):
    """Cancel a running execution."""
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    
    execution = runtime.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status not in ["running", "pending"]:
        raise HTTPException(status_code=400, detail="Can only cancel running or pending executions")
    
    # Update execution status
    execution.status = "cancelled"
    from datetime import datetime
    execution.completed_at = datetime.now()
    execution.error = "Cancelled by user"
    
    return {"execution_id": execution_id, "status": "cancelled"}
