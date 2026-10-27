"""
Agent service - Business logic for agent operations.
"""

from typing import Any

from agent_factory.agents.agent import Agent
from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.engine import RuntimeEngine


class AgentService:
    """Service for agent operations."""

    def __init__(self, registry: LocalRegistry | None = None, runtime: RuntimeEngine | None = None):
        """
        Initialize agent service.

        Args:
            registry: Registry instance (optional)
            runtime: Runtime engine instance (optional)
        """
        self.registry = registry or LocalRegistry()
        self.runtime = runtime or RuntimeEngine()

    def create_agent(self, agent_data: dict[str, Any]) -> Agent:
        """
        Create a new agent.

        Args:
            agent_data: Agent data dictionary

        Returns:
            Created agent
        """
        agent = Agent.from_dict(agent_data)
        self.registry.register_agent(agent)
        self.runtime.register_agent(agent)
        return agent

    def get_agent(self, agent_id: str) -> Agent | None:
        """
        Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent if found, None otherwise
        """
        return self.registry.get_agent(agent_id)

    def list_agents(self, tenant_id: str | None = None) -> list[str]:
        """
        List all agent IDs.

        Args:
            tenant_id: Optional tenant ID filter

        Returns:
            List of agent IDs
        """
        return self.registry.list_agents()

    def update_agent(self, agent_id: str, updates: dict[str, Any]) -> Agent | None:
        """
        Update an agent.

        Args:
            agent_id: Agent ID
            updates: Dictionary of updates

        Returns:
            Updated agent if found, None otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        self.registry.register_agent(agent)
        self.runtime.register_agent(agent)

        return agent

    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted, False if not found
        """
        return self.registry.delete_agent(agent_id)

    def run_agent(self, agent_id: str, input_text: str, session_id: str | None = None) -> str:
        """
        Run an agent.

        Args:
            agent_id: Agent ID
            input_text: Input text
            session_id: Optional session ID

        Returns:
            Execution ID
        """
        # Ensure agent is registered in runtime
        agent = self.get_agent(agent_id)
        if agent:
            self.runtime.register_agent(agent)

        return self.runtime.run_agent(agent_id, input_text, session_id=session_id)
