"""
Tests for workflow visualizer.
"""

from agent_factory.workflows.model import Workflow, WorkflowStep
from agent_factory.workflows.visualizer import to_graphviz, to_mermaid, visualize


def test_to_mermaid():
    """Test Mermaid generation."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[
            WorkflowStep(id="step1", agent_id="agent1"),
            WorkflowStep(id="step2", agent_id="agent2"),
        ],
    )

    mermaid = to_mermaid(workflow)

    assert "graph TD" in mermaid
    assert "Step0" in mermaid
    assert "Step1" in mermaid
    assert "Start" in mermaid
    assert "End" in mermaid


def test_to_graphviz():
    """Test Graphviz generation."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[
            WorkflowStep(id="step1", agent_id="agent1"),
        ],
    )

    dot = to_graphviz(workflow)

    assert "digraph Workflow" in dot
    assert "step0" in dot


def test_visualize(tmp_path):
    """Test visualize function."""
    workflow = Workflow(
        id="test-workflow",
        name="Test Workflow",
        steps=[
            WorkflowStep(id="step1", agent_id="agent1"),
        ],
    )

    output_path = tmp_path / "workflow.md"
    content = visualize(workflow, format="mermaid", output_path=str(output_path))

    assert output_path.exists()
    assert "graph TD" in content
