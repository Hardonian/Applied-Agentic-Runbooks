"""
Integration tests for runtime with prompt logging.
"""

import tempfile
from pathlib import Path

from agent_factory.agents.agent import Agent
from agent_factory.promptlog import SQLiteStorage
from agent_factory.runtime.engine import RuntimeEngine


def test_runtime_with_prompt_logging():
    """Test runtime integration with prompt logging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "promptlog.db"
        storage = SQLiteStorage(str(db_path))

        # Create runtime with prompt logging
        runtime = RuntimeEngine(prompt_log_storage=storage)

        # Create and register agent
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            instructions="You are a test agent.",
        )
        runtime.register_agent(agent)

        # Run agent
        execution_id = runtime.run_agent("test-agent", "test input")

        # Check execution
        execution = runtime.get_execution(execution_id)
        assert execution is not None
        assert execution.status == "completed"

        # Check prompt log
        run = storage.get_run(execution_id)
        assert run is not None
        assert run.agent_id == "test-agent"
        assert run.status == "success"


def test_runtime_agent_registration():
    """Test agent registration in runtime."""
    runtime = RuntimeEngine()

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )

    runtime.register_agent(agent)

    assert "test-agent" in runtime.agents_registry
    assert runtime.agents_registry["test-agent"] == agent
    # Check prompt logging is wired
    assert agent.prompt_log_storage is not None


def test_runtime_execution_listing():
    """Test execution listing."""
    runtime = RuntimeEngine()

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        instructions="Test",
    )
    runtime.register_agent(agent)

    # Run multiple executions
    execution_ids = []
    for i in range(3):
        exec_id = runtime.run_agent("test-agent", f"input {i}")
        execution_ids.append(exec_id)

    # List executions
    executions = runtime.list_executions(entity_id="test-agent", limit=10)

    assert len(executions) == 3

    # Filter by status
    completed = runtime.list_executions(status="completed", limit=10)
    assert len(completed) == 3
