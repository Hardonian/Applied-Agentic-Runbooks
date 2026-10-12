"""Blueprint API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.blueprints.model import Blueprint
from agent_factory.marketplace import publish_blueprint, get_blueprint_details
from agent_factory.marketplace.reviews import get_reviews
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import require_user_permission, Permission

router = APIRouter()
registry = LocalRegistry()


class BlueprintCreate(BaseModel):
    """Blueprint creation model."""
    id: str
    name: str
    version: str
    description: str
    author: str
    agents: Optional[List[Dict[str, Any]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    workflows: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BlueprintInstall(BaseModel):
    """Blueprint installation model."""
    target_path: Optional[str] = None


class BlueprintPublish(BaseModel):
    """Blueprint publish model."""
    is_public: bool = True
    pricing_model: str = "free"
    price: float = 0.0


@router.post("/", response_model=Dict[str, Any])
async def create_blueprint(
    blueprint_data: BlueprintCreate,
    user=Depends(get_current_user)
):
    """Create a new blueprint."""
    require_user_permission(user, Permission.WRITE_AGENTS)
    
    # Check if blueprint already exists
    existing = registry.get_blueprint(blueprint_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Blueprint {blueprint_data.id} already exists")
    
    # Create blueprint from data
    from agent_factory.blueprints.model import (
        BlueprintConfig,
        BlueprintMetadata,
        PricingInfo,
        PricingModel,
    )
    
    config = BlueprintConfig()
    if blueprint_data.config:
        config.dependencies = blueprint_data.config.get("dependencies", [])
        config.environment_variables = blueprint_data.config.get("environment_variables", {})
        config.required_tools = blueprint_data.config.get("required_tools", [])
        config.required_agents = blueprint_data.config.get("required_agents", [])
    
    pricing = PricingInfo(model=PricingModel.FREE)
    if blueprint_data.pricing:
        pricing = PricingInfo(
            model=PricingModel(blueprint_data.pricing.get("model", "free")),
            price=blueprint_data.pricing.get("price", 0.0),
            currency=blueprint_data.pricing.get("currency", "USD"),
            period=blueprint_data.pricing.get("period"),
        )
    
    # Load agents, tools, workflows from data
    agents = []
    if blueprint_data.agents:
        from agent_factory.agents.agent import Agent
        for agent_data in blueprint_data.agents:
            try:
                agents.append(Agent.from_dict(agent_data))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid agent data: {e}")
    
    # Keep component definitions in the portable package manifest. Tool
    # implementations are resolved only from the trusted server-side catalog.
    tools = blueprint_data.tools or []
    workflows = blueprint_data.workflows or []
    
    blueprint = Blueprint(
        id=blueprint_data.id,
        name=blueprint_data.name,
        version=blueprint_data.version,
        description=blueprint_data.description,
        author=blueprint_data.author,
        agents=agents,
        tools=tools,
        workflows=workflows,
        config=config,
        pricing=pricing,
        metadata=BlueprintMetadata(
            demo_url=(blueprint_data.metadata or {}).get("demo_url", ""),
            documentation=(blueprint_data.metadata or {}).get("documentation", ""),
        ),
    )
    
    registry.register_blueprint(blueprint)
    
    return {"id": blueprint.id, "status": "created"}


@router.get("/", response_model=List[str])
def list_blueprints(user=Depends(get_current_user)):
    """List all blueprints."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    return registry.list_blueprints()


@router.get("/{blueprint_id}", response_model=Dict[str, Any])
def get_blueprint(blueprint_id: str, user=Depends(get_current_user)):
    """Get blueprint by ID."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    blueprint = registry.get_blueprint(blueprint_id)
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    return blueprint.to_dict()


@router.post("/{blueprint_id}/install", response_model=Dict[str, Any])
async def install_blueprint(
    blueprint_id: str,
    install_data: BlueprintInstall,
    user=Depends(get_current_user)
):
    """Install a blueprint."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    
    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    # API callers may not choose arbitrary server filesystem destinations.
    # Installations live under the registry's controlled storage root.
    if install_data.target_path:
        raise HTTPException(
            status_code=422,
            detail="target_path is server-managed; omit it to install into the registry workspace.",
        )
    target_path = str(registry.base_path / "installed_blueprints" / blueprint_id)
    
    success = blueprint.install(target_path)
    if not success:
        raise HTTPException(status_code=500, detail="Installation failed")
    
    return {"id": blueprint_id, "status": "installed", "target_path": target_path}


@router.post("/{blueprint_id}/publish", response_model=Dict[str, Any])
async def publish_blueprint_endpoint(
    blueprint_id: str,
    publish_data: BlueprintPublish,
    user=Depends(get_current_user)
):
    """Publish a blueprint to marketplace."""
    require_user_permission(user, Permission.PUBLISH_BLUEPRINTS)
    
    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    publisher_id = user.id if hasattr(user, 'id') else "unknown"
    
    try:
        result = publish_blueprint(
            blueprint=blueprint,
            publisher_id=publisher_id,
            is_public=publish_data.is_public,
            pricing_model=publish_data.pricing_model,
            price=publish_data.price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


@router.get("/{blueprint_id}/reviews", response_model=Dict[str, Any])
def get_blueprint_reviews(
    blueprint_id: str,
    limit: int = 10,
    offset: int = 0,
    user=Depends(get_current_user),
):
    """Get reviews for a blueprint."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    reviews = get_reviews(blueprint_id, limit=limit, offset=offset)
    return reviews
