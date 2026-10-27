"""
Metrics dashboard API routes.

Provides endpoints for metrics dashboard.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel

from agent_factory.telemetry import get_analytics

try:
    from agent_factory.telemetry.revenue import get_revenue_tracker
except ImportError:
    get_revenue_tracker = None  # type: ignore[assignment]

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


class MetricsSummaryResponse(BaseModel):
    """Response for metrics summary."""

    dau: int
    wau: int
    mau: int
    total_tenants: int
    total_users: int
    total_agent_runs: int
    total_workflow_runs: int
    growth_rate: float
    period_start: str
    period_end: str


class RevenueMetricsResponse(BaseModel):
    """Response for revenue metrics."""

    mrr: float
    arr: float
    revenue_by_type: dict
    revenue_by_plan: dict


@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    days: int = Query(30, description="Number of days to include"),
):
    """
    Get overall metrics summary.

    Returns:
        Summary metrics (DAU, WAU, MAU, growth, etc.)
    """
    analytics = get_analytics()

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    summary = analytics.get_growth_summary(start_date, end_date)

    # Get growth rate
    growth = analytics.get_growth_rate("users", "month")

    return MetricsSummaryResponse(
        dau=summary.get("dau", 0),
        wau=summary.get("wau", 0),
        mau=summary.get("mau", 0),
        total_tenants=summary.get("total_tenants", 0),
        total_users=summary.get("total_users", 0),
        total_agent_runs=summary.get("total_agent_runs", 0),
        total_workflow_runs=summary.get("total_workflow_runs", 0),
        growth_rate=growth.get("growth_rate", 0.0),
        period_start=summary.get("period_start", start_date.isoformat()),
        period_end=summary.get("period_end", end_date.isoformat()),
    )


@router.get("/funnel")
async def get_conversion_funnel(
    days: int = Query(30, description="Number of days to include"),
):
    """
    Get conversion funnel metrics.

    Returns:
        Conversion funnel (signup → activated → retained → paying)
    """
    analytics = get_analytics()

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    funnel = analytics.get_conversion_funnel(start_date, end_date)

    return funnel


@router.get("/channels")
async def get_channel_attribution(
    days: int = Query(30, description="Number of days to include"),
):
    """
    Get channel attribution metrics.

    Returns:
        Signups and conversions by channel
    """
    analytics = get_analytics()

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    channels = analytics.get_channel_attribution(start_date, end_date)

    return channels


@router.get("/revenue", response_model=RevenueMetricsResponse)
async def get_revenue_metrics(
    days: int = Query(30, description="Number of days to include"),
):
    """
    Get revenue metrics.

    Returns:
        MRR, ARR, revenue by type and plan
    """
    if get_revenue_tracker is None:
        return RevenueMetricsResponse(
            mrr=0.0,
            arr=0.0,
            revenue_by_type={},
            revenue_by_plan={},
        )

    revenue_tracker = get_revenue_tracker()

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return RevenueMetricsResponse(
        mrr=revenue_tracker.get_mrr(),
        arr=revenue_tracker.get_arr(),
        revenue_by_type=revenue_tracker.get_revenue_by_type(start_date, end_date),
        revenue_by_plan=revenue_tracker.get_revenue_by_plan(start_date, end_date),
    )


@router.get("/retention")
async def get_retention(
    cohort_date: str = Query(..., description="Cohort date (YYYY-MM-DD)"),
    days: list[int] = Query([1, 7, 30], description="Days to check retention"),
):
    """
    Get retention metrics for a cohort.

    Returns:
        Retention rates for specified days
    """
    analytics = get_analytics()

    try:
        cohort_dt = datetime.fromisoformat(cohort_date)
    except ValueError:
        cohort_dt = datetime.strptime(cohort_date, "%Y-%m-%d")

    retention = analytics.get_retention_cohort(cohort_dt, days)

    return {
        "cohort_date": cohort_date,
        "retention": retention,
    }


@router.get("/growth")
async def get_growth_rate(
    metric: str = Query("users", description="Metric to track"),
    period: str = Query("month", description="Period (week, month)"),
):
    """
    Get growth rate for a metric.

    Returns:
        Growth rate and values
    """
    analytics = get_analytics()

    growth = analytics.get_growth_rate(metric, period)

    return growth
