"""
Tests for Speculative Model Cascading and Pareto Cost Optimizer.
"""

import pytest
from agent_factory.optimization.cascade_router import (
    ModelTier,
    SpeculativeCascadeRouter,
)


@pytest.mark.unit
def test_complexity_assessment():
    """Verify task complexity correctly maps to model tier."""
    router = SpeculativeCascadeRouter()

    # Simple prompt
    tier, score = router.assess_complexity("Say hello to Alice.")
    assert tier == ModelTier.FAST
    assert score < 0.45

    # Complex mathematical and distributed system prompt
    tier_complex, score_complex = router.assess_complexity(
        "Formulate a formal verification proof for distributed consensus state replication "
        "and deadlock prevention in a Byzantine fault-tolerant asynchronous network with edge cases."
    )
    assert tier_complex in [ModelTier.STANDARD, ModelTier.DEEP]
    assert score_complex > 0.50


@pytest.mark.unit
def test_speculative_cascade_execution():
    """Verify speculative execution accepts draft and tracks cost savings."""
    router = SpeculativeCascadeRouter()

    result = router.execute("Summarize the quarterly revenue statement.", force_tier=ModelTier.FAST)

    assert result.speculative_draft_accepted is True
    assert result.tier_used == ModelTier.FAST
    assert result.cost_savings_percentage > 50.0
    assert result.speedup_factor >= 1.0
    assert result.verification_score > 0.5

    # Test markdown export
    md = result.to_markdown()
    assert "# ⚡ Speculative Cascade Efficiency Report" in md
    assert "cost reduction" in md
