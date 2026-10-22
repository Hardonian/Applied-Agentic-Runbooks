"""Blueprint search and discovery."""

from typing import Any

from sqlalchemy import or_

from agent_factory.cache import get_cache
from agent_factory.database.models import Blueprint as BlueprintModel
from agent_factory.database.session import get_db


def search_blueprints(
    query: str | None = None,
    category: str | None = None,
    pricing_model: str | None = None,
    min_rating: float | None = None,
    sort_by: str = "popularity",
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Search blueprints in marketplace.

    Args:
        query: Search query
        category: Category filter
        pricing_model: Pricing model filter
        min_rating: Minimum rating filter
        sort_by: Sort field (popularity, rating, downloads, created_at)
        limit: Results limit
        offset: Results offset

    Returns:
        Search results
    """
    cache = get_cache()
    cache_key = f"blueprint_search:{query}:{category}:{pricing_model}:{min_rating}:{sort_by}:{limit}:{offset}"

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    db = next(get_db())

    try:
        # Build query
        q = db.query(BlueprintModel).filter(BlueprintModel.is_public)

        if query:
            q = q.filter(
                or_(
                    BlueprintModel.name.ilike(f"%{query}%"),
                    BlueprintModel.description.ilike(f"%{query}%"),
                )
            )

        if category:
            # Category would be stored in definition JSON
            q = q.filter(BlueprintModel.definition["category"].astext == category)

        if pricing_model:
            q = q.filter(BlueprintModel.pricing_model == pricing_model)

        if min_rating:
            q = q.filter(BlueprintModel.rating >= min_rating)

        # Sort
        if sort_by == "popularity":
            q = q.order_by(BlueprintModel.downloads.desc())
        elif sort_by == "rating":
            q = q.order_by(BlueprintModel.rating.desc())
        elif sort_by == "created_at":
            q = q.order_by(BlueprintModel.created_at.desc())

        # Get total count
        total = q.count()

        # Get results
        blueprints = q.offset(offset).limit(limit).all()

        results = {
            "total": total,
            "offset": offset,
            "limit": limit,
            "blueprints": [
                {
                    "id": bp.id,
                    "name": bp.name,
                    "description": bp.description,
                    "version": bp.version,
                    "pricing_model": bp.pricing_model,
                    "price": bp.price,
                    "rating": bp.rating,
                    "reviews_count": bp.reviews_count,
                    "downloads": bp.downloads,
                    "created_at": bp.created_at.isoformat() if bp.created_at else None,
                }
                for bp in blueprints
            ],
        }

        # Cache results for 5 minutes
        cache.set(cache_key, results, ttl=300)

        return results
    finally:
        db.close()


def get_blueprint_details(blueprint_id: str) -> dict[str, Any] | None:
    """
    Get detailed blueprint information.

    Args:
        blueprint_id: Blueprint ID

    Returns:
        Blueprint details or None
    """
    cache = get_cache()
    cache_key = f"blueprint_details:{blueprint_id}"

    # Try cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    db = next(get_db())

    try:
        blueprint = (
            db.query(BlueprintModel)
            .filter(BlueprintModel.id == blueprint_id, BlueprintModel.is_public)
            .first()
        )

        if not blueprint:
            return None

        result = {
            "id": blueprint.id,
            "name": blueprint.name,
            "description": blueprint.description,
            "version": blueprint.version,
            "definition": blueprint.definition,
            "pricing_model": blueprint.pricing_model,
            "price": blueprint.price,
            "rating": blueprint.rating,
            "reviews_count": blueprint.reviews_count,
            "downloads": blueprint.downloads,
            "created_at": blueprint.created_at.isoformat() if blueprint.created_at else None,
            "updated_at": blueprint.updated_at.isoformat() if blueprint.updated_at else None,
        }

        # Cache for 1 hour
        cache.set(cache_key, result, ttl=3600)

        return result
    finally:
        db.close()
