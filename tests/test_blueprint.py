"""Tests for Blueprint class."""

import tempfile
from pathlib import Path

import pytest

from agent_factory.agents.agent import Agent
from agent_factory.blueprints.model import Blueprint, BlueprintConfig, PricingInfo, PricingModel
from agent_factory.workflows.model import Workflow, WorkflowStep


@pytest.mark.unit
def test_blueprint_creation():
    """Test creating a blueprint."""
    blueprint = Blueprint(
        id="test-blueprint",
        name="Test Blueprint",
        version="1.0.0",
        description="A test blueprint",
        author="Test Author",
    )

    assert blueprint.id == "test-blueprint"
    assert blueprint.name == "Test Blueprint"
    assert blueprint.version == "1.0.0"


@pytest.mark.unit
def test_blueprint_pricing():
    """Test blueprint pricing."""
    pricing = PricingInfo(
        model=PricingModel.SUBSCRIPTION,
        price=99.0,
        currency="USD",
        period="monthly",
    )

    blueprint = Blueprint(
        id="test-blueprint",
        name="Test Blueprint",
        version="1.0.0",
        description="Test",
        author="Test",
        pricing=pricing,
    )

    assert blueprint.pricing.model == PricingModel.SUBSCRIPTION
    assert blueprint.pricing.price == 99.0


@pytest.mark.unit
def test_blueprint_package():
    """Test blueprint packaging."""
    blueprint = Blueprint(
        id="test-blueprint",
        name="Test Blueprint",
        version="1.0.0",
        description="Test",
        author="Test",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = blueprint.package(tmpdir)

        assert Path(package_path).exists()
        assert (Path(package_path) / "blueprint.yaml").exists()


@pytest.mark.unit
def test_blueprint_install():
    """Test blueprint installation."""
    blueprint = Blueprint(
        id="test-blueprint",
        name="Test Blueprint",
        version="1.0.0",
        description="Test",
        author="Test",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = blueprint.install(tmpdir)

        assert result is True
        assert (Path(tmpdir) / "agents").exists()
        assert (Path(tmpdir) / "tools").exists()


@pytest.mark.unit
def test_blueprint_serializes_component_objects_without_python_yaml_tags():
    blueprint = Blueprint(
        id="component-blueprint",
        name="Component Blueprint",
        version="1.0.0",
        description="Test",
        author="Test",
        agents=[Agent(id="agent-1", name="Agent", instructions="Test")],
        tools=[{"id": "tool-1", "name": "Tool"}],
    )

    document = blueprint.to_yaml()

    assert "!!python" not in document
    assert "agent-1" in document
    assert (
        Blueprint.from_dict(__import__("yaml").safe_load(document)["blueprint"]).agents[0]["id"]
        == "agent-1"
    )


@pytest.mark.unit
def test_blueprint_package_writes_portable_component_manifests():
    blueprint = Blueprint(
        id="component-blueprint",
        name="Component Blueprint",
        version="1.0.0",
        description="Test",
        author="Test",
        agents=[Agent(id="agent-1", name="Agent", instructions="Test")],
        tools=[{"id": "tool-1", "name": "Tool", "description": "Test"}],
        workflows=[
            Workflow(
                id="flow-1", name="Flow", steps=[WorkflowStep(id="step-1", agent_id="agent-1")]
            )
        ],
        config=BlueprintConfig(environment_variables={"API_TOKEN": "Token for the provider"}),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        package_path = Path(blueprint.package(tmpdir))

        assert (package_path / "agents" / "agent-1.json").exists()
        assert (package_path / "tools" / "tool-1.json").exists()
        assert (package_path / "workflows" / "flow-1.json").exists()
        assert "API_TOKEN=" in (package_path / ".env.example").read_text()
        assert "Token for the provider=" not in (package_path / ".env.example").read_text()
