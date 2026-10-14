"""Tests for the autonomous arena and red-teaming gauntlet."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from agent_factory.api.main import app
from agent_factory.cli.main import app as cli_app
from agent_factory.evaluation.arena import ArenaRunner, GauntletSuite


@pytest.mark.asyncio
async def test_arena_runner_all_suites():
    """Verify ArenaRunner executes all suites and returns valid metrics."""
    runner = ArenaRunner()
    summary = await runner.run()

    assert summary.status == "passed"
    assert len(summary.suites) == 5
    assert summary.metrics["pass_rate"] == 1.0
    assert summary.metrics["pareto_frontier_score"] > 0.0
    assert "final_merkle_root" in summary.veridag_proof
    assert len(summary.pcap_frames) > 0


@pytest.mark.asyncio
async def test_arena_runner_single_suite():
    """Verify ArenaRunner executes a selected subset."""
    runner = ArenaRunner()
    summary = await runner.run([GauntletSuite.REASONING_FRONTIER])

    assert summary.status == "passed"
    assert len(summary.suites) == 1
    assert summary.suites[0].suite == GauntletSuite.REASONING_FRONTIER


def test_arena_api_endpoints():
    """Verify POST /api/v1/arena/run and GET /api/v1/arena/leaderboard."""
    client = TestClient(app)

    # 1. Trigger run
    response = client.post(
        "/api/v1/arena/run",
        json={"suites": [GauntletSuite.REASONING_FRONTIER.value], "concurrency": 4},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "passed"
    assert "metrics" in data
    assert "veridag_proof" in data

    # 2. Query leaderboard
    board_res = client.get("/api/v1/arena/leaderboard")
    assert board_res.status_code == 200
    board_data = board_res.json()
    assert board_data["count"] >= 1
    assert len(board_data["entries"]) >= 1
    assert "merkle_root" in board_data["entries"][0]


def test_arena_cli_run():
    """Verify agent-factory arena run command."""
    runner = CliRunner()
    result = runner.invoke(cli_app, ["arena", "run", "--suite", "reasoning", "--concurrency", "4"])
    assert result.exit_code == 0
    assert '"status": "passed"' in result.output
