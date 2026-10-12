"""Tool API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.tools.base import Tool
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import require_user_permission, Permission

router = APIRouter()
registry = LocalRegistry()


class ToolCreate(BaseModel):
    """Tool creation model."""
    id: str
    name: str
    description: str
    implementation_code: Optional[str] = None  # For simple tools, code as string
    metadata: Optional[Dict[str, Any]] = None


class ToolUpdate(BaseModel):
    """Tool update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolTestParams(BaseModel):
    """Tool test parameters."""
    params: Dict[str, Any]


@router.post("/", response_model=Dict[str, Any])
async def create_tool(
    tool_data: ToolCreate,
    user=Depends(get_current_user)
):
    """Create a new tool."""
    # Check permission
    require_user_permission(user, Permission.WRITE_AGENTS)
    
    # Check if tool already exists
    existing = registry.get_tool(tool_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool {tool_data.id} already exists")
    
    # Persisted tools are definitions, not an arbitrary code-execution API.
    # Trusted server-side integrations must register their callable during
    # application startup through LocalRegistry.register_tool_implementation.
    if tool_data.implementation_code:
        raise HTTPException(
            status_code=422,
            detail="implementation_code is not accepted. Register a trusted server-side tool implementation instead.",
        )

    def unavailable_implementation(**kwargs):
        raise NotImplementedError(
            f"Tool {tool_data.id} has no registered runtime implementation."
        )
    
    tool = Tool(
        id=tool_data.id,
        name=tool_data.name,
        description=tool_data.description,
        implementation=unavailable_implementation,
    )
    
    if tool_data.metadata:
        from agent_factory.tools.base import ToolMetadata
        tool.metadata = ToolMetadata(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            version=tool_data.metadata.get("version", "1.0.0"),
            author=tool_data.metadata.get("author", user.email if hasattr(user, 'email') else "unknown"),
            category=tool_data.metadata.get("category", "general"),
            tags=tool_data.metadata.get("tags", []),
        )
    
    registry.register_tool(tool)
    
    return {"id": tool.id, "status": "created"}


@router.get("/", response_model=List[str])
def list_tools():
    """List all tools."""
    return registry.list_tools()


@router.get("/{tool_id}", response_model=Dict[str, Any])
def get_tool(tool_id: str):
    """Get tool by ID."""
    tool = registry.get_tool(tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return tool.to_dict()


@router.put("/{tool_id}", response_model=Dict[str, Any])
async def update_tool(
    tool_id: str,
    tool_data: ToolUpdate,
    user=Depends(get_current_user)
):
    """Update a tool."""
    require_user_permission(user, Permission.WRITE_AGENTS)
    
    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Update fields
    if tool_data.name:
        tool.name = tool_data.name
    if tool_data.description:
        tool.description = tool_data.description
    if tool_data.metadata:
        if tool.metadata:
            tool.metadata.version = tool_data.metadata.get("version", tool.metadata.version)
            tool.metadata.author = tool_data.metadata.get("author", tool.metadata.author)
            tool.metadata.category = tool_data.metadata.get("category", tool.metadata.category)
            tool.metadata.tags = tool_data.metadata.get("tags", tool.metadata.tags)
    
    registry.register_tool(tool)
    
    return {"id": tool.id, "status": "updated"}


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    user=Depends(get_current_user)
):
    """Delete a tool."""
    require_user_permission(user, Permission.DELETE_AGENTS)
    
    tool_file = registry.base_path / "tools" / f"{tool_id}.json"
    if not tool_file.exists():
        raise HTTPException(status_code=404, detail="Tool not found")
    
    tool_file.unlink()
    return {"status": "deleted"}


@router.get("/{tool_id}/schema", response_model=Dict[str, Any])
def get_tool_schema(tool_id: str):
    """Get tool schema."""
    tool = registry.get_tool(tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return tool.get_schema()


@router.post("/{tool_id}/test", response_model=Dict[str, Any])
def test_tool(tool_id: str, test_params: ToolTestParams, user=Depends(get_current_user)):
    """Test a tool with given parameters."""
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    tool = registry.get_tool(tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    try:
        result = tool.execute(**test_params.params)
        return {"success": True, "result": result}
    except NotImplementedError as e:
        return {"success": False, "error": str(e), "note": "Tool implementation not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}
