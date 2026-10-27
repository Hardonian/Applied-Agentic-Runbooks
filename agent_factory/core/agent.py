"""
Agent class - Core primitive for creating and running AI agents.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent_factory.core.guardrails import Guardrails
from agent_factory.core.memory import MemoryStore
from agent_factory.core.tool import Tool


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Configuration for an Agent."""

    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    enable_memory: bool = True
    enable_guardrails: bool = True


@dataclass
class AgentResult:
    """Result from agent execution."""

    output: str
    status: AgentStatus
    tokens_used: int = 0
    execution_time: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Handoff:
    """Represents a handoff to another agent."""

    to: "Agent"
    context: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None


class Agent:
    """
    Core Agent class for creating and running AI agents.

    Example:
        >>> agent = Agent(
        ...     id="research-assistant",
        ...     name="Research Assistant",
        ...     instructions="You are a research assistant...",
        ...     tools=[web_search_tool, read_file_tool]
        ... )
        >>> result = agent.run("Find information about Python async")
        >>> print(result.output)
    """

    def __init__(
        self,
        id: str,
        name: str,
        instructions: str,
        tools: list[Tool] | None = None,
        model: str = "gpt-4o",
        memory: MemoryStore | None = None,
        guardrails: Guardrails | None = None,
        config: AgentConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize an Agent.

        Args:
            id: Unique identifier for the agent
            name: Human-readable name
            instructions: System instructions for the agent
            tools: List of tools the agent can use
            model: LLM model to use (default: gpt-4o)
            memory: Memory store for conversation history
            guardrails: Guardrails for safety and validation
            config: Agent configuration
            metadata: Additional metadata
        """
        self.id = id
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.model = model
        self.memory = memory
        self.guardrails = guardrails
        self.config = config or AgentConfig()
        self.metadata = metadata or {}
        self.prompt_log_storage: Any | None = None
        self._status = AgentStatus.IDLE

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent."""
        if tool not in self.tools:
            self.tools.append(tool)

    def remove_tool(self, tool_id: str) -> None:
        """Remove a tool by ID."""
        self.tools = [t for t in self.tools if t.id != tool_id]

    def update_instructions(self, instructions: str) -> None:
        """Update agent instructions."""
        self.instructions = instructions

    def run(
        self,
        input_text: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Run the agent with given input.

        Args:
            input_text: User input/question
            session_id: Optional session ID for memory
            context: Optional context dictionary

        Returns:
            AgentResult with output and metadata
        """
        import time

        start_time = time.time()

        try:
            self._status = AgentStatus.RUNNING

            # Apply guardrails if enabled
            if self.guardrails:
                guardrail_result = self.guardrails.validate_input(input_text)
                if not guardrail_result.allowed:
                    return AgentResult(
                        output="",
                        status=AgentStatus.ERROR,
                        error=f"Input blocked by guardrails: {guardrail_result.reason}",
                    )

            # Load memory if available
            memory_context = {}
            if self.memory and session_id:
                memory_context = self.memory.get_context(session_id)

            # Prepare context
            full_context = {
                **(context or {}),
                **memory_context,
            }

            # Execute agent (this would integrate with OpenAI SDK)
            # For now, this is a placeholder
            output = self._execute_agent(input_text, full_context)

            # Apply output guardrails
            if self.guardrails:
                guardrail_result = self.guardrails.validate_output(output)
                if not guardrail_result.allowed:
                    output = f"[Output modified by guardrails: {guardrail_result.reason}]"

            # Save to memory
            if self.memory and session_id:
                self.memory.save_interaction(session_id, input_text, output)

            execution_time = time.time() - start_time

            self._status = AgentStatus.COMPLETED

            return AgentResult(
                output=output,
                status=AgentStatus.COMPLETED,
                execution_time=execution_time,
                metadata={"model": self.model},
            )

        except Exception as e:
            self._status = AgentStatus.ERROR
            return AgentResult(
                output="",
                status=AgentStatus.ERROR,
                error=str(e),
            )

    def _execute_agent(self, input_text: str, context: dict[str, Any]) -> str:
        """
        Execute the agent using the underlying LLM SDK.

        Args:
            input_text: User input text
            context: Context dictionary

        Returns:
            Agent output text

        Raises:
            RuntimeError: If execution fails
        """
        try:
            from agent_factory.integrations.openai_client import OpenAIAgentClient

            client = OpenAIAgentClient()
            result = client.run_agent(
                instructions=self.instructions,
                input_text=input_text,
                model=self.model,
                tools=self.tools,  # type: ignore[arg-type]
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                context=context,
            )

            return result.get("output", "")
        except ImportError:
            # Fallback if OpenAI SDK not available
            return f"[Agent {self.name} would process: {input_text}]"
        except Exception as e:
            from agent_factory.core.exceptions import AgentExecutionError

            raise AgentExecutionError(f"Agent execution failed: {e!s}") from e

    def handoff(
        self,
        to: "Agent",
        context: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> Handoff:
        """
        Create a handoff to another agent.

        Args:
            to: Target agent
            context: Context to pass to target agent
            reason: Reason for handoff

        Returns:
            Handoff object
        """
        return Handoff(
            to=to,
            context=context or {},
            reason=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "instructions": self.instructions,
            "model": self.model,
            "tools": [tool.id for tool in self.tools],
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], tools_registry: dict[str, Tool] | None = None
    ) -> "Agent":
        """Deserialize agent from dictionary."""
        tools = []
        if tools_registry:
            tools = [tools_registry[tid] for tid in data.get("tools", []) if tid in tools_registry]

        config = AgentConfig(**data.get("config", {}))

        return cls(
            id=data["id"],
            name=data["name"],
            instructions=data["instructions"],
            tools=tools,
            model=data.get("model", "gpt-4o"),
            config=config,
            metadata=data.get("metadata", {}),
        )
