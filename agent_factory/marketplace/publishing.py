"""Blueprint publishing functionality."""

from typing import Any

from agent_factory.blueprints.model import Blueprint
from agent_factory.database.models import Blueprint as BlueprintModel
from agent_factory.database.session import get_db
from agent_factory.marketplace.search import get_blueprint_details
from agent_factory.security.audit import audit_log

__all__ = ["publish_blueprint", "get_blueprint_details"]


def publish_blueprint(
    blueprint: Blueprint,
    publisher_id: str,
    is_public: bool = True,
    pricing_model: str = "free",
    price: float = 0.0
) -> dict[str, Any]:
    """
    Publish blueprint to marketplace.
    
    Args:
        blueprint: Blueprint to publish
        publisher_id: Publisher user ID
        is_public: Whether blueprint is public
        pricing_model: Pricing model (free, one-time, subscription)
        price: Price in USD
        
    Returns:
        Published blueprint info
    """
    db = next(get_db())
    
    try:
        # Check if blueprint already exists
        existing = db.query(BlueprintModel).filter(
            BlueprintModel.id == blueprint.id
        ).first()
        
        if existing:
            # Update existing blueprint
            existing.name = blueprint.name
            existing.description = blueprint.description
            existing.definition = blueprint.to_dict()
            existing.is_public = is_public
            existing.pricing_model = pricing_model
            existing.price = price
            db.commit()
            
            audit_log(
                event_type="blueprint_published",
                user_id=publisher_id,
                resource_type="blueprint",
                resource_id=blueprint.id,
                action="update",
                success=True
            )
            
            return {
                "id": existing.id,
                "status": "updated",
                "version": existing.version
            }
        else:
            # Create new blueprint
            blueprint_model = BlueprintModel(
                id=blueprint.id,
                name=blueprint.name,
                description=blueprint.description or "",
                version="1.0.0",
                definition=blueprint.to_dict(),
                publisher_id=publisher_id,
                is_public=is_public,
                pricing_model=pricing_model,
                price=price
            )
            
            db.add(blueprint_model)
            db.commit()
            
            audit_log(
                event_type="blueprint_published",
                user_id=publisher_id,
                resource_type="blueprint",
                resource_id=blueprint.id,
                action="create",
                success=True
            )
            
            return {
                "id": blueprint_model.id,
                "status": "published",
                "version": blueprint_model.version
            }
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="blueprint_published",
            user_id=publisher_id,
            resource_type="blueprint",
            resource_id=blueprint.id,
            action="create",
            success=False,
            details={"error": str(e)}
        )
        raise


def unpublish_blueprint(blueprint_id: str, publisher_id: str) -> dict[str, Any]:
    """
    Unpublish blueprint from marketplace.
    
    Args:
        blueprint_id: Blueprint ID
        publisher_id: Publisher user ID
        
    Returns:
        Unpublish result
    """
    db = next(get_db())
    
    try:
        blueprint = db.query(BlueprintModel).filter(
            BlueprintModel.id == blueprint_id,
            BlueprintModel.publisher_id == publisher_id
        ).first()
        
        if not blueprint:
            raise ValueError("Blueprint not found or unauthorized")
        
        blueprint.is_public = False
        db.commit()
        
        audit_log(
            event_type="blueprint_unpublished",
            user_id=publisher_id,
            resource_type="blueprint",
            resource_id=blueprint_id,
            action="update",
            success=True
        )
        
        return {"id": blueprint_id, "status": "unpublished"}
    except Exception as e:
        db.rollback()
        audit_log(
            event_type="blueprint_unpublished",
            user_id=publisher_id,
            resource_type="blueprint",
            resource_id=blueprint_id,
            action="update",
            success=False,
            details={"error": str(e)}
        )
        raise
