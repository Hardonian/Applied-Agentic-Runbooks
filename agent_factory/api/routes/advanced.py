"""
Advanced Reasoning, JIT Tooling, Model Cascade, and Substrate Security API Routes.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agent_factory.optimization.cascade_router import ModelTier, SpeculativeCascadeRouter
from agent_factory.reasoning.mcts import SpeculativeMCTSEngine
from agent_factory.security.mcpwall import MCPWall
from agent_factory.tools.jit_synthesizer import JITToolSynthesizer, ToolSynthesisSpec

advanced_router = APIRouter()
_global_mcpwall = MCPWall()


class MCTSSearchRequest(BaseModel):
    problem: str = Field(..., description="Problem statement to resolve via speculative tree search")
    max_depth: int = Field(3, ge=1, le=6)
    branching_factor: int = Field(3, ge=2, le=5)
    num_simulations: int = Field(8, ge=2, le=20)


class CascadeExecuteRequest(BaseModel):
    prompt: str = Field(..., description="Task prompt to execute through speculative cascade")
    force_tier: str | None = Field(None, description="Force tier: fast, standard, deep")


class JITSynthesizeRequest(BaseModel):
    name: str = Field(..., description="Function name for synthesized tool")
    description: str = Field(..., description="Purpose and behavior of the tool")
    code: str | None = Field(None, description="Python code implementation")
    sample_inputs: list[dict[str, Any]] | None = None
    expected_outputs: list[Any] | None = None


class MCPWallValidateRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool name")
    arguments: dict[str, Any] = Field(..., description="Invocation arguments")
    approval_ticket_id: str | None = None


@advanced_router.post("/reasoning/mcts/search", response_model=dict[str, Any])
def search_mcts(request: MCTSSearchRequest):
    """
    Execute Speculative Monte Carlo Tree Search across candidate reasoning hypotheses.
    """
    engine = SpeculativeMCTSEngine(
        max_depth=request.max_depth,
        branching_factor=request.branching_factor,
        num_simulations=request.num_simulations,
    )
    result = engine.search(request.problem)
    return {
        "confidence_score": result.confidence_score,
        "nodes_explored": result.total_nodes_explored,
        "branches_pruned": result.branches_pruned,
        "depth_reached": result.depth_reached,
        "latency_seconds": result.execution_time_seconds,
        "best_trajectory": result.best_trajectory,
        "final_solution": result.final_solution,
        "tree_visualization": result.tree_visualization,
        "markdown_report": result.to_markdown(),
    }


@advanced_router.post("/optimization/cascade/execute", response_model=dict[str, Any])
def execute_cascade(request: CascadeExecuteRequest):
    """
    Execute prompt via Speculative Model Cascade optimizing for Pareto cost and latency.
    """
    tier_enum = None
    if request.force_tier:
        try:
            tier_enum = ModelTier(request.force_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier '{request.force_tier}'")

    router = SpeculativeCascadeRouter()
    res = router.execute(request.prompt, force_tier=tier_enum)
    return {
        "output": res.output,
        "tier_used": res.tier_used.value,
        "model_used": res.model_used,
        "speculative_draft_accepted": res.speculative_draft_accepted,
        "verification_score": res.verification_score,
        "latency_seconds": res.latency_seconds,
        "cost_usd": res.cost_usd,
        "frontier_cost_usd": res.frontier_baseline_cost_usd,
        "cost_savings_percentage": res.cost_savings_percentage,
        "speedup_factor": res.speedup_factor,
        "markdown_report": res.to_markdown(),
    }


@advanced_router.post("/tools/jit/synthesize", response_model=dict[str, Any])
def synthesize_tool(request: JITSynthesizeRequest):
    """
    Synthesize, AST-verify, compile, and sandbox-test a dynamic JIT tool.
    """
    try:
        spec = ToolSynthesisSpec(
            name=request.name,
            description=request.description,
            code=request.code,
            sample_inputs=request.sample_inputs or [],
            expected_outputs=request.expected_outputs,
        )
        tool = JITToolSynthesizer.compile_and_verify(spec)
        return {
            "status": "compiled_and_verified",
            "tool_id": tool.id,
            "tool_name": tool.name,
            "integrity_hash": tool.integrity_hash,
            "source_code": tool.source_code,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JIT Tool synthesis failed: {e!s}",
        )


@advanced_router.post("/security/mcpwall/validate", response_model=dict[str, Any])
def validate_mcp_call(request: MCPWallValidateRequest):
    """
    Inspect tool call against MCPWall zero-trust security boundaries and human gates.
    """
    verdict = _global_mcpwall.validate_tool_call(
        tool_name=request.tool_name,
        arguments=request.arguments,
        approval_ticket_id=request.approval_ticket_id,
    )
    return {
        "allowed": verdict.allowed,
        "reason": verdict.reason,
        "requires_approval": verdict.requires_approval,
        "ticket": {
            "ticket_id": verdict.ticket.ticket_id,
            "tool_name": verdict.ticket.tool_name,
            "request_hash": verdict.ticket.request_hash,
            "expires_at": verdict.ticket.expires_at,
        } if verdict.ticket else None,
    }
