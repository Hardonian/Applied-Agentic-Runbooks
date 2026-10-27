"""Blueprint reviews and ratings."""

from typing import Any

from agent_factory.database.models import Blueprint as BlueprintModel
from agent_factory.database.session import get_db


class Review:
    """Review model."""

    def __init__(self, user_id: str, blueprint_id: str, rating: int, comment: str | None = None):
        self.user_id = user_id
        self.blueprint_id = blueprint_id
        self.rating = rating
        self.comment = comment


def create_review(
    blueprint_id: str, user_id: str, rating: int, comment: str | None = None
) -> dict[str, Any]:
    """
    Create a review for a blueprint.

    Args:
        blueprint_id: Blueprint ID
        user_id: User ID
        rating: Rating (1-5)
        comment: Optional comment

    Returns:
        Created review info
    """
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    db = next(get_db())

    try:
        blueprint = db.query(BlueprintModel).filter(BlueprintModel.id == blueprint_id).first()

        if not blueprint:
            raise ValueError("Blueprint not found")

        # In production, store reviews in separate table
        # For now, update blueprint rating

        # Calculate new rating
        current_rating = blueprint.rating or 0
        current_count = blueprint.reviews_count or 0

        new_count = current_count + 1
        new_rating = float(((current_rating * current_count) + rating) / new_count)

        blueprint.rating = new_rating
        blueprint.reviews_count = new_count
        db.commit()

        # Clear cache
        from agent_factory.cache import get_cache

        cache = get_cache()
        cache.delete(f"blueprint_details:{blueprint_id}")
        cache.clear("blueprint_search:*")

        return {
            "blueprint_id": blueprint_id,
            "rating": rating,
            "comment": comment,
            "status": "created",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_reviews(blueprint_id: str, limit: int = 10, offset: int = 0) -> dict[str, Any]:
    """
    Get reviews for a blueprint.

    Args:
        blueprint_id: Blueprint ID
        limit: Results limit
        offset: Results offset

    Returns:
        Reviews list
    """
    # In production, fetch from reviews table
    # For now, return blueprint rating info
    db = next(get_db())

    try:
        blueprint = db.query(BlueprintModel).filter(BlueprintModel.id == blueprint_id).first()

        if not blueprint:
            return {"total": 0, "reviews": []}

        return {
            "total": blueprint.reviews_count or 0,
            "average_rating": blueprint.rating or 0,
            "reviews": [],  # Would be populated from reviews table
        }
    finally:
        db.close()


def update_rating(blueprint_id: str) -> dict[str, Any]:
    """
    Update blueprint rating based on reviews.

    Args:
        blueprint_id: Blueprint ID

    Returns:
        Updated rating info
    """
    db = next(get_db())

    try:
        blueprint = db.query(BlueprintModel).filter(BlueprintModel.id == blueprint_id).first()

        if not blueprint:
            raise ValueError("Blueprint not found")

        # In production, calculate from reviews table
        # For now, return current rating

        return {
            "blueprint_id": blueprint_id,
            "rating": blueprint.rating or 0,
            "reviews_count": blueprint.reviews_count or 0,
        }
    finally:
        db.close()
