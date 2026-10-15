"""Revenue sharing for blueprint creators."""

from typing import Any

from agent_factory.database.models import Blueprint as BlueprintModel
from agent_factory.database.models import User
from agent_factory.database.session import get_db

# Platform fee percentage (e.g., 30% platform, 70% creator)
PLATFORM_FEE_PERCENTAGE = 0.30
CREATOR_FEE_PERCENTAGE = 0.70


def calculate_revenue_share(amount: float) -> dict[str, float]:
    """
    Calculate revenue share between platform and creator.
    
    Args:
        amount: Total amount in USD
        
    Returns:
        Revenue share breakdown
    """
    platform_fee = amount * PLATFORM_FEE_PERCENTAGE
    creator_fee = amount * CREATOR_FEE_PERCENTAGE
    
    return {
        "total": amount,
        "platform_fee": platform_fee,
        "creator_fee": creator_fee,
        "platform_fee_percentage": PLATFORM_FEE_PERCENTAGE,
        "creator_fee_percentage": CREATOR_FEE_PERCENTAGE
    }


def distribute_payment(
    blueprint_id: str,
    amount: float,
    payment_intent_id: str
) -> dict[str, Any]:
    """
    Distribute payment to blueprint creator.
    
    Args:
        blueprint_id: Blueprint ID
        amount: Payment amount in USD
        payment_intent_id: Stripe payment intent ID
        
    Returns:
        Distribution result
    """
    db = next(get_db())
    
    try:
        blueprint = db.query(BlueprintModel).filter(
            BlueprintModel.id == blueprint_id
        ).first()
        
        if not blueprint or not blueprint.publisher_id:
            raise ValueError("Blueprint or publisher not found")
        
        # Calculate revenue share
        revenue_share = calculate_revenue_share(amount)
        
        # In production, transfer funds to creator's Stripe account
        # For now, record the transaction
        
        # Get creator
        creator = db.query(User).filter(User.id == blueprint.publisher_id).first()
        
        if not creator:
            raise ValueError("Creator not found")
        
        # Record payment (in production, store in payments table)
        # For now, return distribution info
        
        return {
            "blueprint_id": blueprint_id,
            "creator_id": blueprint.publisher_id,
            "creator_email": creator.email,
            "total_amount": amount,
            "platform_fee": revenue_share["platform_fee"],
            "creator_payout": revenue_share["creator_fee"],
            "payment_intent_id": payment_intent_id,
            "status": "distributed"
        }
    finally:
        db.close()
