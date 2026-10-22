"""Telemetry and metrics API routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from agent_factory.security.auth import get_current_user_from_request
from agent_factory.telemetry.analytics import get_analytics

router = APIRouter()


@router.get("/metrics")
async def get_metrics(
    request: Request,
    tenant_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get growth metrics summary.

    Args:
        request: FastAPI request
        tenant_id: Optional tenant ID filter
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)

    Returns:
        Metrics summary
    """
    # Check authentication
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # If tenant_id not provided, use from request state
    if not tenant_id:
        tenant_id = getattr(request.state, "tenant_id", None)

    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format") from None

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format") from None

    analytics = get_analytics()

    if tenant_id:
        metrics = analytics.get_tenant_metrics(
            tenant_id=tenant_id,
            start_date=start_dt,
            end_date=end_dt,
        )
    else:
        metrics = analytics.get_growth_summary(
            start_date=start_dt,
            end_date=end_dt,
        )

    return metrics


@router.get("/metrics/tenant/{tenant_id}")
async def get_tenant_metrics(
    request: Request,
    tenant_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get metrics for a specific tenant.

    Args:
        request: FastAPI request
        tenant_id: Tenant ID
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)

    Returns:
        Tenant metrics
    """
    # Check authentication
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check permission
    from agent_factory.security.rbac import check_permission

    # User must be tenant admin or own the tenant
    if tenant_id:
        user_tenant_id = (
            user.get("tenant_id") if isinstance(user, dict) else getattr(user, "tenant_id", None)
        )
        if user_tenant_id != tenant_id:
            # Check if user is tenant admin
            has_permission = check_permission(user, "view_tenant_metrics", tenant_id)
            if not has_permission:
                raise HTTPException(status_code=403, detail="Permission denied")

    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format") from None

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format") from None

    analytics = get_analytics()
    metrics = analytics.get_tenant_metrics(
        tenant_id=tenant_id,
        start_date=start_dt,
        end_date=end_dt,
    )

    return metrics


@router.get("/funnel")
async def get_conversion_funnel(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get conversion funnel metrics.

    Args:
        request: FastAPI request
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)

    Returns:
        Conversion funnel metrics
    """
    # Check authentication
    user = await get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format") from None

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format") from None

    analytics = get_analytics()
    funnel = analytics.get_conversion_funnel(
        start_date=start_dt,
        end_date=end_dt,
    )

    return funnel
