"""Blueprint API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agent_factory.blueprints.model import Blueprint
from agent_factory.marketplace import publish_blueprint
from agent_factory.marketplace.reviews import get_reviews
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import Permission, require_permission

router = APIRouter()
registry = LocalRegistry()


class BlueprintCreate(BaseModel):
    """Blueprint creation model."""

    id: str
    name: str
    version: str
    description: str
    author: str
    agents: list[dict[str, Any]] | None = None
    tools: list[dict[str, Any]] | None = None
    workflows: list[dict[str, Any]] | None = None
    config: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class BlueprintInstall(BaseModel):
    """Blueprint installation model."""

    target_path: str | None = None


class BlueprintPublish(BaseModel):
    """Blueprint publish model."""

    is_public: bool = True
    pricing_model: str = "free"
    price: float = 0.0


@router.post("/", response_model=dict[str, Any])
async def create_blueprint(blueprint_data: BlueprintCreate, user=Depends(get_current_user)):
    """Create a new blueprint."""
    require_permission(Permission.WRITE_AGENTS)(lambda: None)()

    # Check if blueprint already exists
    existing = registry.get_blueprint(blueprint_data.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Blueprint {blueprint_data.id} already exists")

    # Create blueprint from data
    from agent_factory.blueprints.model import BlueprintConfig, PricingInfo, PricingModel

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
                raise HTTPException(status_code=400, detail=f"Invalid agent data: {e}") from e

    tools = []
    workflows = []

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
        metadata=blueprint_data.metadata or {},
    )

    registry.register_blueprint(blueprint)

    return {"id": blueprint.id, "status": "created"}


@router.get("/", response_model=list[str])
def list_blueprints():
    """List all blueprints."""
    return registry.list_blueprints()


@router.get("/{blueprint_id}", response_model=dict[str, Any])
def get_blueprint(blueprint_id: str):
    """Get blueprint by ID."""
    blueprint = registry.get_blueprint(blueprint_id)

    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    return blueprint.to_dict()


@router.post("/{blueprint_id}/install", response_model=dict[str, Any])
async def install_blueprint(
    blueprint_id: str, install_data: BlueprintInstall, user=Depends(get_current_user)
):
    """Install a blueprint."""
    require_permission(Permission.READ_BLUEPRINTS)(lambda: None)()

    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    target_path = install_data.target_path or "."

    success = blueprint.install(target_path)
    if not success:
        raise HTTPException(status_code=500, detail="Installation failed")

    return {"id": blueprint_id, "status": "installed", "target_path": target_path}


@router.post("/{blueprint_id}/publish", response_model=dict[str, Any])
async def publish_blueprint_endpoint(
    blueprint_id: str, publish_data: BlueprintPublish, user=Depends(get_current_user)
):
    """Publish a blueprint to marketplace."""
    require_permission(Permission.PUBLISH_BLUEPRINTS)(lambda: None)()

    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    publisher_id = user.id if hasattr(user, "id") else "unknown"

    try:
        result = publish_blueprint(
            blueprint=blueprint,
            publisher_id=publisher_id,
            is_public=publish_data.is_public,
            pricing_model=publish_data.pricing_model,
            price=publish_data.price,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}") from e


@router.get("/{blueprint_id}/reviews", response_model=dict[str, Any])
def get_blueprint_reviews(blueprint_id: str, limit: int = 10, offset: int = 0):
    """Get reviews for a blueprint."""
    blueprint = registry.get_blueprint(blueprint_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    reviews = get_reviews(blueprint_id, limit=limit, offset=offset)
    return reviews
