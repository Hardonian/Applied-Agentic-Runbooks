"""
Runtime engine, memory, logging, and configuration.
"""

# Import memory first (doesn't depend on engine)
from agent_factory.runtime.memory import MemoryStore, SQLiteMemoryStore


# Lazy import engine to avoid circular dependency with agents
def __getattr__(name: str):
    """Lazy import for RuntimeEngine and Execution to avoid circular imports."""
    if name == "RuntimeEngine":
        from agent_factory.runtime.engine import RuntimeEngine

        return RuntimeEngine
    elif name == "Execution":
        from agent_factory.runtime.engine import Execution

        return Execution
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "RuntimeEngine",
    "Execution",
    "MemoryStore",
    "SQLiteMemoryStore",
]
