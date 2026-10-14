"""
Tests for Speculative Monte Carlo Tree Search (MCTS) Engine.
"""

import pytest
from agent_factory.reasoning.mcts import (
    MCTSNode,
    SpeculativeMCTSEngine,
)


@pytest.mark.unit
def test_mcts_node_puct_and_q_value():
    """Verify PUCT score computation and state values."""
    node = MCTSNode(thought="Decompose system requirements.", depth=1)
    assert node.q_value == 0.0

    node.visits = 2
    node.value_sum = 1.6
    assert node.q_value == 0.8

    puct = node.puct_score(parent_visits=5, c_puct=1.414)
    assert puct > 0.8


@pytest.mark.unit
def test_speculative_mcts_search():
    """Verify MCTS search runs multi-path simulations, prunes dead ends, and extracts best trajectory."""
    engine = SpeculativeMCTSEngine(
        max_depth=3,
        branching_factor=3,
        num_simulations=12,
        pruning_threshold=0.30,
    )

    result = engine.search("Design a fault-tolerant multi-region state replication architecture.")

    assert result.total_nodes_explored > 1
    assert result.depth_reached >= 2
    assert result.confidence_score > 0.5
    assert len(result.best_trajectory) >= 2
    assert "Verified Solution" in result.final_solution
    assert "tree_visualization" in result.__dict__

    # Test markdown report generation
    md = result.to_markdown()
    assert "# 🧠 Speculative MCTS Reasoning Trajectory" in md
    assert "Pareto-Optimal Reasoning Path" in md
