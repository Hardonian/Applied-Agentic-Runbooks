"""
Research Assistant API Routes - Product Surface.

PRODUCT: Research Assistant
Provides endpoints for:
- Running research queries
- Viewing past research reports
- Downloading reports
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from agent_factory.database.models import Execution as ExecutionModel
from agent_factory.database.session import get_db
from agent_factory.security.auth import get_current_user_from_request
from agent_factory.services.research_service import (
    ResearchReport,
    ResearchRequest,
    get_research_service,
)

router = APIRouter()


@router.post("/research", response_model=ResearchReport)
async def run_research(
    request: ResearchRequest,
    http_request: Request
):
    """
    Run a research query and generate a report.
    
    PRODUCT ENDPOINT: This is the main product surface.
    - Validates inputs against blueprint contract
    - Enforces usage limits (free vs paid)
    - Executes real research logic
    - Returns structured report
    """
    # Get authenticated user
    user = await get_current_user_from_request(http_request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get tenant_id from request state (set by auth middleware)
    tenant_id = getattr(http_request.state, 'tenant_id', None)
    if not tenant_id:
        # Try to get from user's tenant
        db = next(get_db())
        try:
            from agent_factory.database.models import User as UserModel
            user_model = db.query(UserModel).filter(UserModel.id == user.id).first()
            if user_model and user_model.tenant_id:
                tenant_id = user_model.tenant_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User tenant not found"
                )
        finally:
            db.close()
    
    # Run research
    service = get_research_service()
    try:
        report = service.run_research(
            request=request,
            tenant_id=tenant_id,
            user_id=user.id
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research failed: {e!s}"
        )


@router.get("/research/reports", response_model=list[dict[str, Any]])
async def list_reports(
    http_request: Request,
    limit: int = 20,
    offset: int = 0
):
    """
    List past research reports for the authenticated user.
    
    PRODUCT ENDPOINT: View past runs.
    """
    user = await get_current_user_from_request(http_request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get tenant_id
    tenant_id = getattr(http_request.state, 'tenant_id', None)
    if not tenant_id:
        db = next(get_db())
        try:
            from agent_factory.database.models import User as UserModel
            user_model = db.query(UserModel).filter(UserModel.id == user.id).first()
            if user_model and user_model.tenant_id:
                tenant_id = user_model.tenant_id
            else:
                return []
        finally:
            db.close()
    
    # Query executions
    db = next(get_db())
    try:
        executions = db.query(ExecutionModel).filter(
            ExecutionModel.tenant_id == tenant_id,
            ExecutionModel.execution_type == "blueprint",
            ExecutionModel.resource_id == "research-assistant",
            ExecutionModel.status == "completed"
        ).order_by(ExecutionModel.created_at.desc()).offset(offset).limit(limit).all()
        
        reports = []
        for exec in executions:
            if exec.output_data:
                reports.append({
                    "report_id": exec.output_data.get("report_id", exec.id),
                    "query": exec.output_data.get("query", ""),
                    "summary": exec.output_data.get("summary", "")[:200] + "..." if len(exec.output_data.get("summary", "")) > 200 else exec.output_data.get("summary", ""),
                    "generated_at": exec.output_data.get("generated_at", exec.created_at.isoformat()),
                    "execution_time_seconds": exec.execution_time or 0.0
                })
        
        return reports
    finally:
        db.close()


@router.get("/research/reports/{report_id}", response_model=ResearchReport)
async def get_report(
    report_id: str,
    http_request: Request
):
    """
    Get a specific research report by ID.
    
    PRODUCT ENDPOINT: View/download specific report.
    """
    user = await get_current_user_from_request(http_request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get tenant_id
    tenant_id = getattr(http_request.state, 'tenant_id', None)
    if not tenant_id:
        db = next(get_db())
        try:
            from agent_factory.database.models import User as UserModel
            user_model = db.query(UserModel).filter(UserModel.id == user.id).first()
            if user_model and user_model.tenant_id:
                tenant_id = user_model.tenant_id
        finally:
            db.close()
    
    # Find execution
    db = next(get_db())
    try:
        # Try by report_id in output_data first
        db.query(ExecutionModel).filter(
            ExecutionModel.tenant_id == tenant_id,
            ExecutionModel.execution_type == "blueprint",
            ExecutionModel.resource_id == "research-assistant",
            ExecutionModel.status == "completed"
        ).first()
        
        # Search through executions to find matching report_id
        executions = db.query(ExecutionModel).filter(
            ExecutionModel.tenant_id == tenant_id,
            ExecutionModel.execution_type == "blueprint",
            ExecutionModel.resource_id == "research-assistant",
            ExecutionModel.status == "completed"
        ).all()
        
        for exec in executions:
            if exec.output_data and exec.output_data.get("report_id") == report_id:
                return ResearchReport(**exec.output_data)
            if exec.id == report_id and exec.output_data:
                return ResearchReport(**exec.output_data)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    finally:
        db.close()


@router.get("/research/usage", response_model=dict[str, Any])
async def get_usage_info(
    http_request: Request
):
    """
    Get usage information for the authenticated user.
    
    PRODUCT ENDPOINT: Check usage limits and remaining quota.
    """
    user = await get_current_user_from_request(http_request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get tenant_id
    tenant_id = getattr(http_request.state, 'tenant_id', None)
    if not tenant_id:
        db = next(get_db())
        try:
            from agent_factory.database.models import User as UserModel
            user_model = db.query(UserModel).filter(UserModel.id == user.id).first()
            if user_model and user_model.tenant_id:
                tenant_id = user_model.tenant_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User tenant not found"
                )
        finally:
            db.close()
    
    # Get usage info
    service = get_research_service()
    try:
        limit_info = service._check_usage_limits(tenant_id, user.id)
        
        # Get current month usage
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        db = next(get_db())
        try:
            executions_this_month = db.query(ExecutionModel).filter(
                ExecutionModel.tenant_id == tenant_id,
                ExecutionModel.execution_type == "blueprint",
                ExecutionModel.resource_id == "research-assistant",
                ExecutionModel.created_at >= month_start,
                ExecutionModel.status == "completed"
            ).count()
        finally:
            db.close()
        
        return {
            "plan_type": limit_info['plan_type'],
            "used": executions_this_month,
            "limit": limit_info['limit'],
            "remaining": limit_info['remaining'],
            "reset_date": (month_start + timedelta(days=32)).replace(day=1).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage info: {e!s}"
        )
