"""Tests for Agent CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agent_factory.cli.commands.agent import app


@pytest.mark.unit
def test_cli_agent_create():
    """Test creating an agent via CLI."""
    runner = CliRunner()

    with patch("agent_factory.cli.commands.agent.LocalRegistry") as mock_registry_class:
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry

        result = runner.invoke(
            app,
            [
                "create",
                "test-cli-agent",
                "--name",
                "Test CLI Agent",
                "--instructions",
                "You are a test agent.",
            ],
        )

        assert result.exit_code == 0
        assert "Created agent" in result.stdout
        mock_registry.register_agent.assert_called_once()


@pytest.mark.unit
def test_cli_agent_list():
    """Test listing agents via CLI."""
    runner = CliRunner()

    with patch("agent_factory.cli.commands.agent.LocalRegistry") as mock_registry_class:
        mock_registry = MagicMock()
        mock_registry.list_agents.return_value = ["agent-1", "agent-2"]
        mock_registry.get_agent.return_value = MagicMock(name="Test Agent")
        mock_registry_class.return_value = mock_registry

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Agents:" in result.stdout
        mock_registry.list_agents.assert_called_once()


@pytest.mark.unit
def test_cli_agent_list_empty():
    """Test listing agents when none exist."""
    runner = CliRunner()

    with patch("agent_factory.cli.commands.agent.LocalRegistry") as mock_registry_class:
        mock_registry = MagicMock()
        mock_registry.list_agents.return_value = []
        mock_registry_class.return_value = mock_registry

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No agents found" in result.stdout


@pytest.mark.unit
@patch("agent_factory.cli.commands.agent.LocalRegistry")
def test_cli_agent_run(mock_registry_class):
    """Test running an agent via CLI."""
    runner = CliRunner()

    mock_registry = MagicMock()
    mock_agent = MagicMock()
    mock_result = MagicMock()
    mock_result.status.value = "completed"
    mock_result.output = "Test output"
    mock_agent.run.return_value = mock_result
    mock_registry.get_agent.return_value = mock_agent
    mock_registry_class.return_value = mock_registry

    result = runner.invoke(
        app,
        [
            "run",
            "test-agent",
            "--input",
            "Hello",
        ],
    )

    assert result.exit_code == 0
    assert "Test output" in result.stdout
    mock_agent.run.assert_called_once()


@pytest.mark.unit
@patch("agent_factory.cli.commands.agent.LocalRegistry")
def test_cli_agent_run_not_found(mock_registry_class):
    """Test running a non-existent agent."""
    runner = CliRunner()

    mock_registry = MagicMock()
    mock_registry.get_agent.return_value = None
    mock_registry_class.return_value = mock_registry

    result = runner.invoke(
        app,
        [
            "run",
            "non-existent",
            "--input",
            "Hello",
        ],
    )

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


@pytest.mark.unit
@patch("agent_factory.cli.commands.agent.LocalRegistry")
def test_cli_agent_delete(mock_registry_class):
    """Test deleting an agent via CLI."""
    runner = CliRunner()

    mock_registry = MagicMock()
    mock_registry.delete_agent.return_value = True
    mock_registry_class.return_value = mock_registry

    result = runner.invoke(app, ["delete", "test-agent"])

    assert result.exit_code == 0
    assert "Deleted agent" in result.stdout
    mock_registry.delete_agent.assert_called_once_with("test-agent")


@pytest.mark.unit
@patch("agent_factory.cli.commands.agent.LocalRegistry")
def test_cli_agent_delete_not_found(mock_registry_class):
    """Test deleting a non-existent agent."""
    runner = CliRunner()

    mock_registry = MagicMock()
    mock_registry.delete_agent.return_value = False
    mock_registry_class.return_value = mock_registry

    result = runner.invoke(app, ["delete", "non-existent"])

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()
