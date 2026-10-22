"""
Anthropic Claude SDK integration for Agent Factory Platform.
"""

import os
from typing import Any

from anthropic import Anthropic

from agent_factory.tools.base import Tool


class AnthropicAgentClient:
    """
    Client for interacting with Anthropic Claude API.

    This wraps the Anthropic SDK to provide agent execution capabilities.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=self.api_key)

    def run_agent(
        self,
        instructions: str,
        input_text: str,
        model: str = "claude-3-5-sonnet-20241022",
        tools: list[Tool] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an agent using Anthropic Claude API.

        Args:
            instructions: System instructions for the agent
            input_text: User input
            model: Model to use
            tools: List of tools available to the agent
            temperature: Temperature setting
            max_tokens: Maximum tokens
            context: Additional context

        Returns:
            Agent execution result
        """
        # Build messages
        messages = [{"role": "user", "content": input_text}]

        # Convert tools to Anthropic format
        anthropic_tools = []
        if tools:
            for tool in tools:
                tool_schema = tool.get_schema()
                anthropic_tools.append(
                    {
                        "name": tool.id,
                        "description": tool.description,
                        "input_schema": tool_schema.get("parameters", {}),
                    }
                )

        # Build system message with instructions
        system_message = instructions
        if context:
            system_message += f"\n\nContext: {context}"

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=messages,
                tools=anthropic_tools if anthropic_tools else None,
            )

            # Extract content
            output = ""
            tool_calls = []

            for content_block in response.content:
                if content_block.type == "text":
                    output += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append(
                        {
                            "id": content_block.id,
                            "name": content_block.name,
                            "input": content_block.input,
                        }
                    )

            return {
                "output": output,
                "tool_calls": tool_calls,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": model,
            }
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}") from e

    def stream_agent(
        self,
        instructions: str,
        input_text: str,
        model: str = "claude-3-5-sonnet-20241022",
        tools: list[Tool] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context: dict[str, Any] | None = None,
    ):
        """
        Stream agent execution using Anthropic Claude API.

        Args:
            instructions: System instructions
            input_text: User input
            model: Model to use
            tools: Available tools
            temperature: Temperature setting
            max_tokens: Maximum tokens
            context: Additional context

        Yields:
            Chunks of agent output
        """
        messages = [{"role": "user", "content": input_text}]

        anthropic_tools = []
        if tools:
            for tool in tools:
                tool_schema = tool.get_schema()
                anthropic_tools.append(
                    {
                        "name": tool.id,
                        "description": tool.description,
                        "input_schema": tool_schema.get("parameters", {}),
                    }
                )

        system_message = instructions
        if context:
            system_message += f"\n\nContext: {context}"

        try:
            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=messages,
                tools=anthropic_tools if anthropic_tools else None,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield event.delta.text
        except Exception as e:
            raise RuntimeError(f"Anthropic API streaming error: {str(e)}") from e
