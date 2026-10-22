"""
Referral system API routes.

Handles referral code generation, tracking, and rewards.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from agent_factory.telemetry import ReferralEvent, get_collector

router = APIRouter(prefix="/api/v1/referrals", tags=["referrals"])


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
    user_id: str,  # TODO: Get from auth
    tenant_id: str,  # TODO: Get from auth
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

    # Track referral code generation (optional event)
    get_collector()

    return ReferralCodeResponse(
        referral_code=referral_code,
        share_url=share_url,
        created_at=datetime.utcnow(),
    )


@router.post("/send")
async def send_referral(
    request: SendReferralRequest,
    user_id: str,  # TODO: Get from auth
    tenant_id: str,  # TODO: Get from auth
):
    """
    Send a referral to someone.

    This tracks that a referral was sent (for metrics).
    Actual email sending would be handled by email service.
    """
    collector = get_collector()

    # Track referral sent event
    event = ReferralEvent(
        event_id=str(uuid.uuid4()),
        referral_code=request.referral_code,
        referral_type="sent",
        tenant_id=tenant_id,
        user_id=user_id,
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
    user_id: str,  # TODO: Get from auth
    tenant_id: str,  # TODO: Get from auth
):
    """
    Get statistics for a referral code.

    Returns:
        Total sent, converted, conversion rate, rewards granted
    """
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
    new_user_id: str,  # TODO: Get from auth (new user)
    new_tenant_id: str,  # TODO: Get from auth (new tenant)
):
    """
    Mark a referral as converted (when new user signs up).

    This should be called when a new user signs up with a referral code.
    """
    collector = get_collector()

    # Find the referrer (user who sent this code)
    # TODO: Store referral_code -> referrer_user_id mapping in database
    # For now, we'll track the conversion event

    # Track referral converted event
    event = ReferralEvent(
        event_id=str(uuid.uuid4()),
        referral_code=referral_code,
        referral_type="converted",
        referred_user_id=new_user_id,
        tenant_id=new_tenant_id,
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
        "referred_user_id": new_user_id,
    }
