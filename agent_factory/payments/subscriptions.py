"""Subscription management."""

from typing import Any

from agent_factory.payments.stripe_client import StripeClient


def create_subscription(customer_id: str, blueprint_id: str, price_id: str) -> dict[str, Any]:
    """
    Create subscription for blueprint.

    Args:
        customer_id: Customer ID
        blueprint_id: Blueprint ID
        price_id: Stripe price ID

    Returns:
        Subscription object
    """
    client = StripeClient()

    subscription = client.create_subscription(
        customer_id=customer_id, price_id=price_id, metadata={"blueprint_id": blueprint_id}
    )

    return {
        "subscription_id": subscription.id,
        "status": subscription.status,
        "blueprint_id": blueprint_id,
    }


def cancel_subscription(subscription_id: str) -> dict[str, Any]:
    """
    Cancel subscription.

    Args:
        subscription_id: Subscription ID

    Returns:
        Cancellation result
    """
    import stripe

    subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)

    return {
        "subscription_id": subscription_id,
        "status": "cancelled",
        "cancel_at": subscription.cancel_at,
    }


def get_subscription(subscription_id: str) -> dict[str, Any] | None:
    """
    Get subscription details.

    Args:
        subscription_id: Subscription ID

    Returns:
        Subscription object or None
    """
    import stripe

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }
    except stripe.error.InvalidRequestError:
        return None
