"""Registry-backed portable export/import tests."""

from pathlib import Path

from agent_factory.agents.agent import Agent
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.utils.export_import import export_agent, export_workflow, import_agent, import_workflow
from agent_factory.workflows.model import Workflow, WorkflowStep


def test_agent_export_import_round_trip(tmp_path: Path):
    source = LocalRegistry(str(tmp_path / "source"))
    source.register_agent(Agent(id="agent-1", name="Agent", instructions="Test"))
    artifact = export_agent("agent-1", tmp_path / "agent.yaml", registry=source)

    destination = LocalRegistry(str(tmp_path / "destination"))
    assert import_agent(artifact, registry=destination) == "agent-1"
    assert destination.get_agent("agent-1").instructions == "Test"


def test_workflow_export_import_round_trip(tmp_path: Path):
    source = LocalRegistry(str(tmp_path / "source"))
    source.register_workflow(
        Workflow(id="flow-1", name="Flow", steps=[WorkflowStep(id="step-1", agent_id="agent-1")])
    )
    artifact = export_workflow("flow-1", tmp_path / "flow.json", format="json", registry=source)

    destination = LocalRegistry(str(tmp_path / "destination"))
    assert import_workflow(artifact, registry=destination) == "flow-1"
    assert destination.get_workflow("flow-1").steps[0].agent_id == "agent-1"
