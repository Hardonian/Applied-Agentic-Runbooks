"""Subscription management."""

from typing import Any, cast

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

    sub_data = cast(Any, subscription)
    return {
        "subscription_id": (
            sub_data.get("id") if isinstance(sub_data, dict) else getattr(sub_data, "id", None)
        ),
        "status": (
            sub_data.get("status")
            if isinstance(sub_data, dict)
            else getattr(sub_data, "status", None)
        ),
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
        sub_obj = cast(Any, subscription)
        return {
            "id": getattr(sub_obj, "id", None)
            or (sub_obj.get("id") if isinstance(sub_obj, dict) else None),
            "status": getattr(sub_obj, "status", None)
            or (sub_obj.get("status") if isinstance(sub_obj, dict) else None),
            "current_period_end": getattr(sub_obj, "current_period_end", None)
            or (sub_obj.get("current_period_end") if isinstance(sub_obj, dict) else None),
            "cancel_at_period_end": getattr(sub_obj, "cancel_at_period_end", None)
            or (sub_obj.get("cancel_at_period_end") if isinstance(sub_obj, dict) else None),
        }
    except stripe.error.InvalidRequestError:
        return None
