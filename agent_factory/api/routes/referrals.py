"""
Referral system API routes.

Handles referral code generation, tracking, and rewards.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from agent_factory.security.auth import User, get_current_user
from agent_factory.security.rbac import Permission, require_user_permission
from agent_factory.telemetry import ReferralEvent, get_collector

router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])
_referral_owners: dict[str, dict[str, str]] = {}


class ReferralCodeResponse(BaseModel):
    """Response for referral code generation."""
    referral_code: str
    share_url: str
    created_at: datetime


class ReferralStatsResponse(BaseModel):
    """Response for referral statistics."""
    referral_code: str
    total_sent: int
    total_converted: int
    conversion_rate: float
    rewards_granted: int


class SendReferralRequest(BaseModel):
    """Request to send a referral."""
    referral_code: str
    recipient_email: str | None = None
    recipient_name: str | None = None


@router.post("/generate", response_model=ReferralCodeResponse)
async def generate_referral_code(
    user: User = Depends(get_current_user),
):
    """
    Generate a referral code for a user.
    
    Returns:
        Referral code and share URL
    """
    # Generate unique referral code
    referral_code = f"REF-{uuid.uuid4().hex[:8].upper()}"
    
    # Create share URL
    share_url = f"https://agentfactory.io/signup?ref={referral_code}"
    
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant is required for referrals")
    _referral_owners[referral_code] = {"user_id": user.id, "tenant_id": user.tenant_id}
    
    return ReferralCodeResponse(
        referral_code=referral_code,
        share_url=share_url,
        created_at=datetime.now(timezone.utc),
    )


@router.post("/send")
async def send_referral(
    request: SendReferralRequest,
    user: User = Depends(get_current_user),
):
    """
    Send a referral to someone.
    
    This tracks that a referral was sent (for metrics).
    Actual email sending would be handled by email service.
    """
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    owner = _referral_owners.get(request.referral_code)
    if not owner or owner["user_id"] != user.id or owner["tenant_id"] != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code not found")
    collector = get_collector()
    
    # Track referral sent event
    event = ReferralEvent(
        event_id=str(uuid.uuid4()),
        referral_code=request.referral_code,
        referral_type="sent",
        tenant_id=user.tenant_id,
        user_id=user.id,
    )
    
    collector.record_event(event)
    
    # TODO: Send email via email service
    # email_service.send_referral_email(
    #     to=request.recipient_email,
    #     referral_code=request.referral_code,
    #     referrer_name=request.recipient_name,
    # )
    
    return {"status": "sent", "referral_code": request.referral_code}


@router.get("/stats/{referral_code}", response_model=ReferralStatsResponse)
async def get_referral_stats(
    referral_code: str,
    user: User = Depends(get_current_user),
):
    """
    Get statistics for a referral code.
    
    Returns:
        Total sent, converted, conversion rate, rewards granted
    """
    require_user_permission(user, Permission.READ_ANALYTICS)
    owner = _referral_owners.get(referral_code)
    if not owner or owner["user_id"] != user.id or owner["tenant_id"] != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code not found")
    collector = get_collector()
    
    # Query referral events for this code
    events = collector.query_events(
        event_type=None,  # Get all events, filter below
        limit=10000,
    )
    
    sent_count = 0
    converted_count = 0
    rewards_granted = 0
    
    for event in events:
        if isinstance(event, ReferralEvent) and event.referral_code == referral_code:
            if event.referral_type == "sent":
                sent_count += 1
            elif event.referral_type == "converted":
                converted_count += 1
                if event.reward_granted:
                    rewards_granted += 1
    
    conversion_rate = converted_count / sent_count if sent_count > 0 else 0.0
    
    return ReferralStatsResponse(
        referral_code=referral_code,
        total_sent=sent_count,
        total_converted=converted_count,
        conversion_rate=conversion_rate,
        rewards_granted=rewards_granted,
    )


@router.post("/convert/{referral_code}")
async def convert_referral(
    referral_code: str,
    user: User = Depends(get_current_user),
):
    """
    Mark a referral as converted (when new user signs up).
    
    This should be called when a new user signs up with a referral code.
    """
    require_user_permission(user, Permission.EXECUTE_AGENTS)
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant is required for referrals")
    if referral_code not in _referral_owners:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code not found")
    collector = get_collector()
    
    # Find the referrer (user who sent this code)
    # TODO: Store referral_code -> referrer_user_id mapping in database
    # For now, we'll track the conversion event
    
    # Track referral converted event
    event = ReferralEvent(
        event_id=str(uuid.uuid4()),
        referral_code=referral_code,
        referral_type="converted",
        referred_user_id=user.id,
        tenant_id=user.tenant_id,
        reward_granted=False,  # Will be granted by reward service
    )
    
    collector.record_event(event)
    
    # TODO: Grant rewards to referrer and referred user
    # reward_service.grant_referral_rewards(
    #     referral_code=referral_code,
    #     referrer_user_id=referrer_user_id,
    #     referred_user_id=new_user_id,
    # )
    
    return {
        "status": "converted",
        "referral_code": referral_code,
        "referred_user_id": user.id,
    }
