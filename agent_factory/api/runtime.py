"""Process-local runtime shared by all REST API route modules.

The registry persists definitions, while the runtime owns in-flight and
recent execution state.  Routes must use this single instance so execution
status, retries, and cancellation refer to the same execution records.
"""

from agent_factory.runtime.engine import RuntimeEngine

runtime = RuntimeEngine()
