"""
Research Assistant Service - Product execution layer.

PRODUCT: Research Assistant
TARGET USER: Researchers, analysts, students, professionals
CORE JOB: Generate comprehensive research reports from queries
OUTPUT: Structured research report with summary, findings, sources, citations
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator

from agent_factory.agents.agent import Agent, AgentResult
from agent_factory.billing.usage_tracker import get_usage_tracker
from agent_factory.database.models import Execution as ExecutionModel
from agent_factory.database.models import Plan, Subscription, Tenant
from agent_factory.database.session import get_db
from agent_factory.integrations.tools.web_search import web_search


# PRODUCT CONTRACT - Input Schema
class ResearchRequest(BaseModel):
    """Research request input schema - PRODUCT CONTRACT."""
    query: str = Field(..., min_length=10, max_length=1000, description="Research question or topic")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of search results")
    include_citations: bool = Field(default=True, description="Include source citations")
    depth: str = Field(default="standard", description="Research depth: quick, standard, or comprehensive")
    
    @validator('depth')
    def validate_depth(cls, v):
        allowed = ['quick', 'standard', 'comprehensive']
        if v not in allowed:
            raise ValueError(f'depth must be one of {allowed}')
        return v


# PRODUCT CONTRACT - Output Schema
class ResearchReport(BaseModel):
    """Research report output schema - PRODUCT CONTRACT."""
    report_id: str
    query: str
    summary: str
    key_findings: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    citations: list[str]
    generated_at: str
    execution_time_seconds: float


class ResearchService:
    """
    Research Assistant execution service.
    
    Handles:
    - Input validation against blueprint contract
    - Usage limit enforcement (free vs paid)
    - Safe execution of research logic
    - Output formatting per contract
    - Execution logging and auditability
    """
    
    BLUEPRINT_ID = "research-assistant"
    FREE_TIER_REPORTS_PER_MONTH = 5
    FREE_TIER_MAX_RESULTS = 5
    FREE_TIER_DEPTH_LEVELS = ['quick']
    
    def __init__(self):
        """Initialize research service."""
        self.usage_tracker = get_usage_tracker()
    
    def _check_usage_limits(self, tenant_id: str, user_id: str) -> dict[str, Any]:
        """
        Check if user has exceeded usage limits.
        
        Returns:
            Dict with 'allowed', 'plan_type', 'remaining', 'limit'
        
        Raises:
            HTTPException: If limit exceeded
        """
        db = next(get_db())
        try:
            # Get tenant
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tenant not found"
                )
            
            plan_type = tenant.plan or "free"
            
            # Get active subscription
            subscription = db.query(Subscription).filter(
                Subscription.tenant_id == tenant_id,
                Subscription.status == "active"
            ).first()
            
            if subscription:
                plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
                if plan:
                    plan_type = str(plan.plan_type or "free")
            
            # Check if pro/paid plan
            is_paid = plan_type in ['pro', 'enterprise', 'paid']
            
            if is_paid:
                return {
                    'allowed': True,
                    'plan_type': plan_type,
                    'remaining': float('inf'),
                    'limit': float('inf')
                }
            
            # Free tier: check monthly usage
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Count executions this month
            executions_this_month = db.query(ExecutionModel).filter(
                ExecutionModel.tenant_id == tenant_id,
                ExecutionModel.execution_type == "blueprint",
                ExecutionModel.resource_id == self.BLUEPRINT_ID,
                ExecutionModel.created_at >= month_start,
                ExecutionModel.status == "completed"
            ).count()
            
            remaining = max(0, self.FREE_TIER_REPORTS_PER_MONTH - executions_this_month)
            
            if executions_this_month >= self.FREE_TIER_REPORTS_PER_MONTH:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Usage limit exceeded",
                        "message": f"Free tier allows {self.FREE_TIER_REPORTS_PER_MONTH} reports per month. Upgrade to Pro for unlimited reports.",
                        "limit": self.FREE_TIER_REPORTS_PER_MONTH,
                        "used": executions_this_month,
                        "upgrade_url": "/api/v1/payments/upgrade"
                    }
                )
            
            return {
                'allowed': True,
                'plan_type': plan_type,
                'remaining': remaining,
                'limit': self.FREE_TIER_REPORTS_PER_MONTH
            }
        finally:
            db.close()
    
    def _validate_free_tier_constraints(self, request: ResearchRequest, plan_type: str) -> None:
        """Validate that free tier requests don't exceed allowed parameters."""
        if plan_type == "free":
            if request.max_results > self.FREE_TIER_MAX_RESULTS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Feature not available on free tier",
                        "message": f"Free tier allows max {self.FREE_TIER_MAX_RESULTS} results. Upgrade to Pro for up to 20 results.",
                        "upgrade_url": "/api/v1/payments/upgrade"
                    }
                )
            
            if request.depth not in self.FREE_TIER_DEPTH_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Feature not available on free tier",
                        "message": "Free tier allows 'quick' depth only. Upgrade to Pro for 'standard' and 'comprehensive' depth.",
                        "upgrade_url": "/api/v1/payments/upgrade"
                    }
                )
    
    def _execute_research(self, request: ResearchRequest) -> ResearchReport:
        """
        Execute research and generate report.
        
        This is the REAL execution - not mocked.
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Web search
            search_results = web_search(request.query, num_results=request.max_results)
            
            # Step 2: Create research agent
            agent = Agent(
                id="research-assistant-agent",
                name="Research Assistant",
                instructions=f"""You are a research assistant. Analyze the search results and generate a comprehensive research report.

Query: {request.query}
Depth: {request.depth}

Generate:
1. Executive summary (2-3 paragraphs)
2. Key findings (3-5 bullet points with sources)
3. Analysis based on search results
4. Citations from sources

Be thorough and cite sources when possible.""",
                tools=[web_search],
                model="gpt-4o",
                config=None  # Use defaults
            )
            
            # Step 3: Run agent with search context
            prompt = f"""Based on these search results, generate a comprehensive research report:

{search_results}

Query: {request.query}
Depth: {request.depth}

Provide:
1. Executive summary
2. Key findings with sources
3. Analysis
4. Citations"""
            
            result: AgentResult = agent.run(prompt)
            
            # Step 4: Parse and structure output
            output = result.output
            
            # Extract structured data from output
            summary = self._extract_summary(output)
            findings = self._extract_findings(output, search_results)
            sources = self._extract_sources(search_results)
            citations = self._extract_citations(output, sources)
            
            execution_time = time.time() - start_time
            
            return ResearchReport(
                report_id=str(uuid.uuid4()),
                query=request.query,
                summary=summary,
                key_findings=findings,
                sources=sources,
                citations=citations,
                generated_at=datetime.utcnow().isoformat(),
                execution_time_seconds=round(execution_time, 2)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research execution failed: {e!s}"
            )
    
    def _extract_summary(self, output: str) -> str:
        """Extract summary from agent output."""
        # Simple extraction - look for summary section
        if "Summary:" in output or "Executive Summary:" in output:
            lines = output.split('\n')
            summary_lines = []
            in_summary = False
            for line in lines:
                if "Summary:" in line or "Executive Summary:" in line:
                    in_summary = True
                    summary_lines.append(line.split(':', 1)[-1].strip())
                elif in_summary:
                    if line.strip() and not line.startswith('#'):
                        summary_lines.append(line.strip())
                    elif line.startswith('#'):
                        break
            
            return '\n'.join(summary_lines) if summary_lines else output[:500]
        
        # Fallback: first 500 chars
        return output[:500] + "..." if len(output) > 500 else output
    
    def _extract_findings(self, output: str, search_results: str) -> list[dict[str, Any]]:
        """Extract key findings from output."""
        findings = []
        
        # Look for findings section
        if "Key Findings:" in output or "Findings:" in output:
            lines = output.split('\n')
            in_findings = False
            current_finding: dict[str, Any] | None = None
            
            for line in lines:
                if "Key Findings:" in line or "Findings:" in line:
                    in_findings = True
                    continue
                
                if in_findings:
                    stripped = line.strip()
                    if stripped.startswith(('-', '*', '•')):
                        if current_finding:
                            findings.append(current_finding)
                        current_finding = {
                            'finding': stripped.lstrip('-*• ').strip(),
                            'source': 'Research results',
                            'relevance_score': 0.8
                        }
                    elif current_finding and stripped:
                        current_finding['finding'] += ' ' + stripped
            
            if current_finding:
                findings.append(current_finding)
        
        # Fallback: create from output
        if not findings:
            findings = [{
                'finding': output[:200] + "..." if len(output) > 200 else output,
                'source': 'Research results',
                'relevance_score': 0.8
            }]
        
        return findings[:5]  # Max 5 findings
    
    def _extract_sources(self, search_results: str) -> list[dict[str, Any]]:
        """Extract sources from search results."""
        sources = []
        lines = search_results.split('\n')
        
        current_source: dict[str, Any] = {}
        for line in lines:
            if line.strip().startswith('-'):
                if current_source:
                    sources.append(current_source)
                current_source = {'title': '', 'url': '', 'snippet': ''}
                title = line.lstrip('- ').strip()
                current_source['title'] = title
            elif 'http' in line:
                current_source['url'] = line.strip()
            elif current_source and line.strip():
                current_source['snippet'] = line.strip()
        
        if current_source:
            sources.append(current_source)
        
        return sources[:10]  # Max 10 sources
    
    def _extract_citations(self, output: str, sources: list[dict[str, Any]]) -> list[str]:
        """Extract citations from output."""
        citations = []
        
        # Extract URLs from output
        import re
        urls = re.findall(r'https?://[a-zA-Z0-9_.~:/?#\[\]@!$&()*+,;=%-]+', output)
        citations.extend(urls)
        
        # Add source URLs
        for source in sources:
            if source.get('url') and source['url'] not in citations:
                citations.append(source['url'])
        
        return citations[:10]  # Max 10 citations
    
    def run_research(
        self,
        request: ResearchRequest,
        tenant_id: str,
        user_id: str
    ) -> ResearchReport:
        """
        Run research with full validation and execution.
        
        Args:
            request: Research request
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Research report
            
        Raises:
            HTTPException: If validation fails or execution fails
        """
        # Step 1: Check usage limits
        limit_info = self._check_usage_limits(tenant_id, user_id)
        
        # Step 2: Validate free tier constraints
        self._validate_free_tier_constraints(request, limit_info['plan_type'])
        
        # Step 3: Create execution record
        execution_id = str(uuid.uuid4())
        db = next(get_db())
        try:
            execution = ExecutionModel(
                id=execution_id,
                execution_type="blueprint",
                resource_id=self.BLUEPRINT_ID,
                status="running",
                input_data=request.dict(),
                tenant_id=tenant_id,
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.add(execution)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create execution record: {e!s}"
            )
        finally:
            db.close()
        
        # Step 4: Execute research
        try:
            report = self._execute_research(request)
            
            # Step 5: Save execution result
            db = next(get_db())
            try:
                exec_record = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
                if exec_record:
                    exec_record.status = "completed"
                    exec_record.output_data = report.dict()
                    exec_record.completed_at = datetime.utcnow()
                    exec_record.execution_time = report.execution_time_seconds
                    db.commit()
                
                # Track usage
                self.usage_tracker.record_agent_run(
                    tenant_id=tenant_id,
                    tokens_used=0,  # Would track actual tokens
                    cost_estimate=0.0,
                )
            finally:
                db.close()
            
            return report
            
        except HTTPException:
            raise
        except Exception as e:
            # Mark execution as failed
            db = next(get_db())
            try:
                exec_record = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
                if exec_record:
                    exec_record.status = "failed"
                    exec_record.error = str(e)
                    exec_record.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research execution failed: {e!s}"
            )


# Global service instance
_research_service: ResearchService | None = None


def get_research_service() -> ResearchService:
    """Get global research service instance."""
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service
