"""Payments API routes."""

import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel

from agent_factory.payments.stripe_client import create_checkout_session, handle_webhook
from agent_factory.payments.subscriptions import create_subscription, cancel_subscription, get_subscription
from agent_factory.payments.revenue_sharing import calculate_revenue_share, distribute_payment
from agent_factory.security.auth import get_current_user
from agent_factory.security.rbac import require_user_permission, Permission

router = APIRouter()


class CheckoutRequest(BaseModel):
    """Checkout request."""
    blueprint_id: str
    success_url: str
    cancel_url: str


class SubscriptionRequest(BaseModel):
    """Subscription request."""
    customer_id: str
    blueprint_id: str
    price_id: str


@router.post("/checkout", response_model=Dict[str, Any])
async def create_checkout(
    request: CheckoutRequest,
    user=Depends(get_current_user)
):
    """Create checkout session for blueprint purchase."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    
    from agent_factory.marketplace.search import get_blueprint_details
    blueprint = get_blueprint_details(request.blueprint_id)
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    price = blueprint.get("price", 0.0)
    if price <= 0:
        raise HTTPException(status_code=400, detail="Blueprint is free")
    
    customer_email = user.email if hasattr(user, 'email') else None
    
    session = create_checkout_session(
        blueprint_id=request.blueprint_id,
        price=price,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        customer_email=customer_email
    )
    
    return session


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    result = handle_webhook(request)
    return result


@router.post("/subscription", response_model=Dict[str, Any])
async def create_subscription_endpoint(
    request: SubscriptionRequest,
    user=Depends(get_current_user)
):
    """Create subscription for blueprint."""
    require_user_permission(user, Permission.MANAGE_BILLING)
    
    subscription = create_subscription(
        customer_id=request.customer_id,
        blueprint_id=request.blueprint_id,
        price_id=request.price_id
    )
    
    return subscription


@router.post("/subscription/{subscription_id}/cancel", response_model=Dict[str, Any])
async def cancel_subscription_endpoint(
    subscription_id: str,
    user=Depends(get_current_user)
):
    """Cancel subscription."""
    require_user_permission(user, Permission.MANAGE_BILLING)
    
    result = cancel_subscription(subscription_id)
    return result


@router.get("/subscription/{subscription_id}", response_model=Dict[str, Any])
async def get_subscription_endpoint(
    subscription_id: str,
    user=Depends(get_current_user)
):
    """Get subscription details."""
    require_user_permission(user, Permission.MANAGE_BILLING)
    
    subscription = get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription


@router.get("/revenue-share/{blueprint_id}", response_model=Dict[str, Any])
async def get_revenue_share(
    blueprint_id: str,
    amount: float,
    user=Depends(get_current_user)
):
    """Calculate revenue share for blueprint."""
    require_user_permission(user, Permission.READ_BLUEPRINTS)
    
    revenue_share = calculate_revenue_share(amount)
    return revenue_share


@router.post("/upgrade", response_model=Dict[str, Any])
async def upgrade_to_pro(
    request: Request,
    user=Depends(get_current_user)
):
    """
    Upgrade user to Pro plan.
    
    PRODUCT ENDPOINT: Upgrade from free to paid tier.
    Creates Stripe checkout session for Pro subscription ($29/month).
    """
    from agent_factory.database.session import get_db
    from agent_factory.database.models import User as UserModel, Tenant, Plan
    from agent_factory.payments.stripe_client import StripeClient
    
    db = next(get_db())
    try:
        # Get user and tenant
        user_model = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not user_model:
            raise HTTPException(status_code=404, detail="User not found")
        
        tenant = db.query(Tenant).filter(Tenant.id == user_model.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Check if already on pro plan
        if tenant.plan in ['pro', 'paid', 'enterprise']:
            return {
                "status": "already_upgraded",
                "message": "User is already on a paid plan",
                "plan": tenant.plan
            }
        
        # Get or create Pro plan
        pro_plan = db.query(Plan).filter(Plan.plan_type == "pro").first()
        if not pro_plan:
            # Create Pro plan
            pro_plan = Plan(
                id="pro-plan",
                name="Pro Plan",
                plan_type="pro",
                price_monthly=29.0,
                price_yearly=290.0,  # 10 months price
                currency="USD",
                features={
                    "unlimited_reports": True,
                    "max_results": 20,
                    "all_depth_levels": True
                },
                limits={
                    "reports_per_month": -1,  # -1 = unlimited
                    "max_results_per_report": 20
                },
                is_active=True
            )
            db.add(pro_plan)
            db.commit()
        
        # Create or get Stripe customer
        stripe_customer = None
        try:
            if not os.getenv("STRIPE_SECRET_KEY"):
                # In test mode without Stripe key, grant pro plan immediately
                tenant.plan = "pro"
                sub = db.query(Subscription).filter(
                    Subscription.tenant_id == tenant.id
                ).first()
                if not sub:
                    sub = Subscription(
                        tenant_id=tenant.id,
                        plan_id=pro_plan.id,
                        status="active",
                        billing_cycle="monthly"
                    )
                    db.add(sub)
                else:
                    sub.plan_id = pro_plan.id
                    sub.status = "active"
                db.commit()
                return {
                    "status": "test_mode",
                    "message": "Stripe not configured. In test mode, upgrade would be granted.",
                    "checkout_url": None,
                    "test_mode": True
                }

            stripe_client = StripeClient()
            existing_sub = db.query(Subscription).filter(
                Subscription.tenant_id == tenant.id,
                Subscription.stripe_customer_id.isnot(None)
            ).first()
            
            if existing_sub and existing_sub.stripe_customer_id:
                import stripe
                stripe_customer = stripe.Customer.retrieve(existing_sub.stripe_customer_id)
            else:
                stripe_customer = stripe_client.create_customer(
                    email=user_model.email,
                    name=user_model.email
                )
        except Exception as e:
            # If Stripe not configured, return test mode response
            if not os.getenv("STRIPE_SECRET_KEY"):
                tenant.plan = "pro"
                db.commit()
                return {
                    "status": "test_mode",
                    "message": "Stripe not configured. In test mode, upgrade would be granted.",
                    "checkout_url": None,
                    "test_mode": True
                }
            raise
        
        # Create checkout session for subscription
        import stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Research Assistant Pro",
                        "description": "Unlimited research reports, up to 20 results, all depth levels"
                    },
                    "unit_amount": 2900,  # $29.00 in cents
                    "recurring": {
                        "interval": "month"
                    }
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{request.base_url}api/v1/payments/upgrade/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.base_url}api/v1/payments/upgrade/cancel",
            customer=stripe_customer.id,
            metadata={
                "tenant_id": tenant.id,
                "user_id": user_model.id,
                "plan_id": pro_plan.id
            }
        )
        
        return {
            "status": "checkout_created",
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Upgrade failed: {str(e)}"
        )
    finally:
        db.close()


@router.get("/upgrade/success", response_model=Dict[str, Any])
async def upgrade_success(
    session_id: str,
    request: Request
):
    """
    Handle successful upgrade checkout.
    
    PRODUCT ENDPOINT: Complete upgrade after Stripe payment.
    """
    import stripe
    from agent_factory.database.session import get_db
    from agent_factory.database.models import Tenant, Subscription, Plan
    
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    
    if not stripe.api_key:
        # Test mode - just grant upgrade
        return {
            "status": "upgraded",
            "message": "Upgrade granted (test mode)",
            "plan": "pro"
        }
    
    try:
        # Retrieve checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != "paid":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        tenant_id = session.metadata.get("tenant_id")
        plan_id = session.metadata.get("plan_id")
        
        db = next(get_db())
        try:
            # Update tenant plan
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                tenant.plan = "pro"
                db.commit()
            
            # Create subscription record
            subscription = Subscription(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                plan_id=plan_id,
                status="active",
                billing_cycle="monthly",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                stripe_subscription_id=session.subscription,
                stripe_customer_id=session.customer
            )
            db.add(subscription)
            db.commit()
            
            return {
                "status": "upgraded",
                "message": "Successfully upgraded to Pro plan",
                "plan": "pro"
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upgrade: {str(e)}"
        )
