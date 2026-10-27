"""
OpenAI Agents SDK integration for Agent Factory Platform.
"""

import json
import os
from typing import Any

from openai import OpenAI

from agent_factory.tools.base import Tool


class OpenAIAgentClient:
    """
    Client for interacting with OpenAI Agents SDK.

    This wraps the OpenAI SDK to provide agent execution capabilities.
    """

    def __init__(
        self,
        api_key: str | None = None,
        client: Any | None = None,
        timeout_seconds: float = 30.0,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")

        self.client = client or OpenAI(
            api_key=self.api_key,
            timeout=timeout_seconds,
            # The SDK retries transient connection/rate-limit failures. The
            # circuit breaker below protects the platform after repeated ones.
            max_retries=2,
        )

    def run_agent(
        self,
        instructions: str,
        input_text: str,
        model: str = "gpt-4o",
        tools: list[Tool] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an agent using OpenAI API with circuit breaker protection.

        Args:
            instructions: System instructions for the agent
            input_text: User input
            model: Model to use (default: "gpt-4o")
            tools: List of tools available to the agent (optional)
            temperature: Temperature setting (default: 0.7)
            max_tokens: Maximum tokens (default: 2000)
            context: Optional conversation context (optional)

        Returns:
            Dictionary with output, tool_calls, tokens_used, and model

        Raises:
            ValueError: If API key is not configured
            Exception: If API call fails (wrapped by circuit breaker)
        """
        # Convert tools to OpenAI format
        openai_tools = []
        if tools:
            for tool in tools:
                tool_schema = tool.get_schema()
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.id,
                            "description": tool.description,
                            "parameters": tool_schema.get("parameters", {}),
                        },
                    }
                )

        # Build messages
        messages = [{"role": "system", "content": instructions}]

        # Add context if provided
        if context and "messages" in context:
            messages.extend(context["messages"][-10:])  # Last 10 messages

        # Add user input
        messages.append({"role": "user", "content": input_text})

        # Call OpenAI API with circuit breaker protection
        from agent_factory.security.circuit_breaker import CircuitBreakerConfig, get_circuit_breaker

        breaker = get_circuit_breaker(
            "openai_api",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60.0,
            ),
        )

        response = breaker.call(
            self.client.chat.completions.create,
            model=model,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract response
        message = response.choices[0].message
        output = message.content or ""

        # Handle tool calls if any
        tool_calls = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append(
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    }
                )

        return {
            "output": output,
            "tool_calls": tool_calls,
            "tokens_used": getattr(response.usage, "total_tokens", 0) if response.usage else 0,
            "model": model,
        }

    def stream_agent(
        self,
        instructions: str,
        input_text: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context: dict[str, Any] | None = None,
    ):
        """Yield text deltas from a streamed OpenAI completion."""
        messages = [{"role": "system", "content": instructions}]
        if context and "messages" in context:
            messages.extend(context["messages"][-10:])
        messages.append({"role": "user", "content": input_text})

        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            choices = getattr(chunk, "choices", [])
            if not choices:
                continue
            content = getattr(getattr(choices[0], "delta", None), "content", None)
            if content:
                yield content

    def execute_tool_call(
        self,
        tool: Tool,
        arguments: Any,
    ) -> Any:
        """
        Execute a tool call.

        Args:
            tool: Tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Tool call arguments must be valid JSON") from exc
        if not isinstance(arguments, dict):
            raise ValueError("Tool call arguments must be a JSON object")
        return tool.execute(**arguments)
