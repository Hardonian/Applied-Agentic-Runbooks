"""
Billing plan management.
"""

from typing import Any

from agent_factory.database.models import Plan as PlanModel
from agent_factory.database.session import get_db


def get_plan(plan_id: str) -> dict[str, Any] | None:
    """
    Get plan by ID.

    Args:
        plan_id: Plan ID

    Returns:
        Plan info or None
    """
    db = next(get_db())

    try:
        plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
        if not plan:
            return None

        return {
            "id": plan.id,
            "name": plan.name,
            "plan_type": plan.plan_type,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "currency": plan.currency,
            "features": plan.features or {},
            "limits": plan.limits or {},
        }
    finally:
        db.close()


def list_plans() -> list[dict[str, Any]]:
    """
    List all active plans.

    Returns:
        List of plans
    """
    db = next(get_db())

    try:
        plans = db.query(PlanModel).filter(PlanModel.is_active).all()

        return [
            {
                "id": plan.id,
                "name": plan.name,
                "plan_type": plan.plan_type,
                "price_monthly": plan.price_monthly,
                "price_yearly": plan.price_yearly,
                "currency": plan.currency,
                "features": plan.features or {},
                "limits": plan.limits or {},
            }
            for plan in plans
        ]
    finally:
        db.close()


def create_plan(
    plan_id: str,
    name: str,
    plan_type: str,
    price_monthly: float = 0.0,
    price_yearly: float = 0.0,
    currency: str = "USD",
    features: dict[str, Any] | None = None,
    limits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a new billing plan.

    Args:
        plan_id: Plan ID
        name: Plan name
        plan_type: Plan type (free, pro, enterprise)
        price_monthly: Monthly price
        price_yearly: Yearly price
        currency: Currency code
        features: Plan features
        limits: Plan limits

    Returns:
        Created plan info
    """
    db = next(get_db())

    try:
        plan = PlanModel(
            id=plan_id,
            name=name,
            plan_type=plan_type,
            price_monthly=price_monthly,
            price_yearly=price_yearly,
            currency=currency,
            features=features or {},
            limits=limits or {},
            is_active=True,
        )

        db.add(plan)
        db.commit()

        return {
            "id": plan.id,
            "name": plan.name,
            "plan_type": plan.plan_type,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "currency": plan.currency,
            "features": plan.features or {},
            "limits": plan.limits or {},
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
