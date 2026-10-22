"""Tests for registry deserialization."""

import json

import pytest

from agent_factory.registry.local_registry import LocalRegistry


@pytest.mark.unit
def test_get_tool_deserialization():
    """Test tool deserialization from registry."""
    registry = LocalRegistry()

    # Create a test tool file
    tool_data = {
        "id": "test-tool",
        "name": "Test Tool",
        "description": "A test tool",
        "schema": {
            "type": "function",
            "parameters": {
                "type": "object",
                "properties": {"x": {"type": "string", "description": "Input x"}},
                "required": ["x"],
            },
        },
        "metadata": {"version": "1.0.0", "author": "test", "category": "test", "tags": ["test"]},
    }

    tool_file = registry.base_path / "tools" / "test-tool.json"
    tool_file.write_text(json.dumps(tool_data))

    try:
        tool = registry.get_tool("test-tool")
        assert tool is not None
        assert tool.id == "test-tool"
        assert tool.name == "Test Tool"
        assert tool.metadata is not None
        assert tool.metadata.version == "1.0.0"
    finally:
        if tool_file.exists():
            tool_file.unlink()


@pytest.mark.unit
def test_get_workflow_deserialization():
    """Test workflow deserialization from registry."""
    registry = LocalRegistry()

    # Create a test workflow file
    workflow_data = {
        "id": "test-workflow",
        "name": "Test Workflow",
        "steps": [
            {
                "id": "step1",
                "agent_id": "agent1",
                "input_mapping": {},
                "output_mapping": {},
                "condition": {"expression": "true", "description": "Always run"},
                "timeout": 30,
                "retry_attempts": 3,
            }
        ],
        "triggers": [{"type": "manual", "config": {}, "enabled": True}],
        "branching": {},
    }

    workflow_file = registry.base_path / "workflows" / "test-workflow.json"
    workflow_file.write_text(json.dumps(workflow_data))

    try:
        workflow = registry.get_workflow("test-workflow")
        assert workflow is not None
        assert workflow.id == "test-workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].id == "step1"
        assert workflow.steps[0].condition is not None
    finally:
        if workflow_file.exists():
            workflow_file.unlink()
