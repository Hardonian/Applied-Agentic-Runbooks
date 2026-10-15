"""
Tests for memory store implementations.
"""

import os
import tempfile

import pytest

from agent_factory.runtime.memory import (
    RedisMemoryStore,
    SQLiteMemoryStore,
    get_memory_store,
)


def test_sqlite_memory_store_save_interaction():
    """Test SQLite memory store save interaction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "memory.db")
        store = SQLiteMemoryStore(db_path=db_path)
        
        store.save_interaction(
            session_id="test-session",
            input_text="Hello",
            output_text="Hi there!",
            metadata={"test": True},
        )
        
        context = store.get_context("test-session")
        assert len(context["recent_interactions"]) == 1
        assert context["recent_interactions"][0]["input"] == "Hello"


def test_sqlite_memory_store_get_history():
    """Test SQLite memory store get history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "memory.db")
        store = SQLiteMemoryStore(db_path=db_path)
        
        store.save_interaction("test-session", "Hello", "Hi!")
        store.save_interaction("test-session", "How are you?", "I'm good!")
        
        history = store.get_history("test-session")
        
        assert len(history) == 2
        assert history[0].input_text == "Hello"
        assert history[1].input_text == "How are you?"


def test_sqlite_memory_store_clear_session():
    """Test SQLite memory store clear session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "memory.db")
        store = SQLiteMemoryStore(db_path=db_path)
        
        store.save_interaction("test-session", "Hello", "Hi!")
        store.clear_session("test-session")
        
        history = store.get_history("test-session")
        assert len(history) == 0


def test_get_memory_store_sqlite():
    """Test get memory store SQLite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "memory.db")
        store = get_memory_store("sqlite", db_path=db_path)
        
        assert isinstance(store, SQLiteMemoryStore)


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not available"
)
def test_get_memory_store_redis():
    """Test get memory store Redis."""
    try:
        store = get_memory_store("redis")
        assert isinstance(store, RedisMemoryStore)
    except (ImportError, ValueError):
        pytest.skip("Redis not available")
