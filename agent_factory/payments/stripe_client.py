"""Stripe payment integration."""

import os
from typing import Any, cast

import stripe
from fastapi import HTTPException, Request, status

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class StripeClient:
    """Stripe client wrapper."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize Stripe client.

        Args:
            api_key: Stripe API key (optional, uses env var if not provided)
        """
        if api_key:
            stripe.api_key = api_key
        elif not stripe.api_key:
            raise ValueError("Stripe API key not configured")

    def create_customer(self, email: str, name: str | None = None) -> dict[str, Any]:
        """
        Create Stripe customer.

        Args:
            email: Customer email
            name: Customer name

        Returns:
            Customer object
        """
        customer_kwargs: dict[str, Any] = {"email": email}
        if name:
            customer_kwargs["name"] = name
        customer = stripe.Customer.create(**customer_kwargs)
        return cast(dict[str, Any], customer)

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Create payment intent.

        Args:
            amount: Amount in cents
            currency: Currency code
            customer_id: Customer ID
            metadata: Additional metadata

        Returns:
            Payment intent object
        """
        intent_kwargs: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "metadata": metadata or {},
        }
        if customer_id:
            intent_kwargs["customer"] = customer_id
        intent = stripe.PaymentIntent.create(**intent_kwargs)
        return cast(dict[str, Any], intent)

    def create_subscription(
        self, customer_id: str, price_id: str, metadata: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Create subscription.

        Args:
            customer_id: Customer ID
            price_id: Stripe price ID
            metadata: Additional metadata

        Returns:
            Subscription object
        """
        subscription = stripe.Subscription.create(
            customer=customer_id, items=[{"price": price_id}], metadata=metadata or {}
        )
        return cast(dict[str, Any], subscription)


def create_checkout_session(
    blueprint_id: str,
    price: float,
    success_url: str,
    cancel_url: str,
    customer_email: str | None = None,
) -> dict[str, Any]:
    """
    Create Stripe checkout session for blueprint purchase.

    Args:
        blueprint_id: Blueprint ID
        price: Price in USD
        success_url: Success redirect URL
        cancel_url: Cancel redirect URL
        customer_email: Customer email

    Returns:
        Checkout session object
    """
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing not configured",
        )

    session_params: dict[str, Any] = {
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Blueprint: {blueprint_id}",
                    },
                    "unit_amount": int(price * 100),  # Convert to cents
                },
                "quantity": 1,
            }
        ],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "blueprint_id": blueprint_id,
        },
    }
    if customer_email:
        session_params["customer_email"] = customer_email

    session = stripe.checkout.Session.create(**cast(Any, session_params))

    return {"session_id": session.id, "url": session.url}


def handle_webhook(request: Request) -> dict[str, Any]:
    """
    Handle Stripe webhook events.

    Args:
        request: FastAPI request

    Returns:
        Webhook processing result
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook secret not configured"
        )

    payload = request.body
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            cast(Any, payload), cast(Any, sig_header), webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    # Handle event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        blueprint_id = session.get("metadata", {}).get("blueprint_id")

        if blueprint_id:
            # Process blueprint purchase
            from agent_factory.marketplace.search import get_blueprint_details

            blueprint = get_blueprint_details(blueprint_id)

            if blueprint:
                # Update download count
                from agent_factory.database.models import Blueprint as BlueprintModel
                from agent_factory.database.session import get_db

                db = next(get_db())

                try:
                    bp = db.query(BlueprintModel).filter(BlueprintModel.id == blueprint_id).first()

                    if bp:
                        bp.downloads = (bp.downloads or 0) + 1
                        db.commit()
                finally:
                    db.close()

    return {"status": "processed", "event_type": event["type"]}
