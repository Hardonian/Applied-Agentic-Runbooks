"""
Financial management API endpoints.
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_factory.financial.cost_tracker import (
    CostType,
    get_cost_tracker,
)

router = APIRouter()


class CostRecordRequest(BaseModel):
    """Cost record request."""

    cost_type: str
    amount: float
    entity_type: str
    entity_id: str
    metadata: dict | None = None


class BudgetRequest(BaseModel):
    """Budget request."""

    name: str
    entity_type: str
    entity_id: str
    amount: float
    period: str = "monthly"
    alert_threshold: float = 0.8


@router.post("/costs")
async def record_cost(request: CostRecordRequest):
    """Record a cost event."""
    tracker = get_cost_tracker()

    try:
        cost_type = CostType(request.cost_type)
        record_id = tracker.record_cost(
            cost_type=cost_type,
            amount=Decimal(str(request.amount)),
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            metadata=request.metadata,
        )

        return JSONResponse(
            content={"record_id": record_id, "status": "recorded"},
            status_code=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/costs/{entity_type}/{entity_id}")
async def get_costs(
    entity_type: str,
    entity_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get costs for an entity."""
    tracker = get_cost_tracker()

    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    total = tracker.get_total_cost(entity_type, entity_id, start, end)
    breakdown = tracker.get_cost_breakdown(entity_type, entity_id, start, end)

    return JSONResponse(
        content={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "total_cost": float(total),
            "breakdown": {k: float(v) for k, v in breakdown.items()},
        }
    )


@router.post("/budgets")
async def create_budget(request: BudgetRequest):
    """Create a budget."""
    tracker = get_cost_tracker()

    budget_id = tracker.create_budget(
        name=request.name,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        amount=Decimal(str(request.amount)),
        period=request.period,
        alert_threshold=Decimal(str(request.alert_threshold)),
    )

    return JSONResponse(
        content={"budget_id": budget_id, "status": "created"},
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/budgets/{budget_id}")
async def get_budget_status(budget_id: str):
    """Get budget status."""
    tracker = get_cost_tracker()

    try:
        status_data = tracker.get_budget_status(budget_id)
        return JSONResponse(content=status_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/costs/estimate")
async def estimate_cost(
    entity_type: str,
    entity_id: str,
    tokens: int,
    model: str = "gpt-4o",
):
    """Estimate cost based on tokens."""
    tracker = get_cost_tracker()

    estimated_cost = tracker.estimate_cost(
        entity_type=entity_type,
        entity_id=entity_id,
        tokens=tokens,
        model=model,
    )

    return JSONResponse(
        content={
            "estimated_cost": float(estimated_cost),
            "tokens": tokens,
            "model": model,
        }
    )
