"""
Tests for prompt logging.
"""

import tempfile
from pathlib import Path

from agent_factory.promptlog import SQLiteStorage, diff_runs
from agent_factory.promptlog.model import PromptLogEntry
from agent_factory.promptlog.model import Run as RunModel


def test_sqlite_storage():
    """Test SQLite storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLiteStorage(str(db_path))
        
        # Create a run
        run = RunModel(
            run_id="test-run-1",
            agent_id="test-agent",
            inputs={"input": "test"},
            outputs={"output": "result"},
            status="success",
            execution_time=1.5,
            tokens_used=100,
        )
        
        # Save
        storage.save_run(run)
        
        # Retrieve
        retrieved = storage.get_run("test-run-1")
        
        assert retrieved is not None
        assert retrieved.run_id == "test-run-1"
        assert retrieved.agent_id == "test-agent"
        assert retrieved.status == "success"
        assert retrieved.execution_time == 1.5


def test_list_runs():
    """Test listing runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLiteStorage(str(db_path))
        
        # Create multiple runs
        for i in range(5):
            run = RunModel(
                run_id=f"run-{i}",
                agent_id="test-agent",
                inputs={"input": f"test {i}"},
                outputs={"output": f"result {i}"},
                status="success",
            )
            storage.save_run(run)
        
        # List runs
        runs = storage.list_runs(limit=10)
        
        assert len(runs) == 5
        
        # Filter by agent
        filtered = storage.list_runs(filters={"agent_id": "test-agent"}, limit=10)
        assert len(filtered) == 5


def test_prompt_entry():
    """Test prompt log entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLiteStorage(str(db_path))
        
        # Create run
        run = RunModel(
            run_id="test-run",
            agent_id="test-agent",
            inputs={},
            outputs={},
            status="success",
        )
        storage.save_run(run)
        
        # Create prompt entry
        entry = PromptLogEntry(
            run_id="test-run",
            step=1,
            prompt="test prompt",
            response="test response",
        )
        storage.save_prompt_entry(entry)
        
        # Retrieve entries
        entries = storage.get_prompt_entries("test-run")
        
        assert len(entries) == 1
        assert entries[0].prompt == "test prompt"
        assert entries[0].response == "test response"


def test_diff_runs():
    """Test diff runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = SQLiteStorage(str(db_path))
        
        # Create two runs
        run1 = RunModel(
            run_id="run-1",
            agent_id="test-agent",
            inputs={"input": "test"},
            outputs={"output": "result1"},
            status="success",
            execution_time=1.0,
            tokens_used=50,
        )
        run2 = RunModel(
            run_id="run-2",
            agent_id="test-agent",
            inputs={"input": "test"},
            outputs={"output": "result2"},
            status="success",
            execution_time=2.0,
            tokens_used=100,
        )
        
        storage.save_run(run1)
        storage.save_run(run2)
        
        # Diff
        diff_result = diff_runs("run-1", "run-2", storage)
        
        assert "run1_id" in diff_result
        assert "run2_id" in diff_result
        assert "metrics_diff" in diff_result
        assert diff_result["metrics_diff"]["execution_time"]["diff"] == 1.0
