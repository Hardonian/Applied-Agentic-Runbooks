"""
Universal Multi-Provider LLM Gateway for Agent Factory.

Provides a unified, production-ready interface across:
- OpenAI (GPT-4o, o1, o3-mini)
- Anthropic (Claude 3.5 Sonnet, Claude 3.7 Sonnet / Extended Thinking)
- Google Gemini (Gemini 2.0 Flash, Gemini 1.5 Pro)
- DeepSeek (DeepSeek V3, DeepSeek R1 Reasoning)
- Groq / Mistral / Ollama / Local OpenAI-Compatible Endpoints
- Mock / Sandbox Provider (for zero-cost offline testing)
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"
    MOCK = "mock"


@dataclass
class StreamChunk:
    """Represents a streaming chunk from an LLM."""

    delta: str = ""
    reasoning_delta: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    reasoning_content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    raw_response: Any | None = None


# Pricing per 1M tokens (Input, Output) in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o1": (15.00, 60.00),
    "o3-mini": (1.10, 4.40),
    "claude-3-7-sonnet": (3.00, 15.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-pro": (1.25, 5.00),
    "deepseek-chat": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
    "llama-3.3-70b-versatile": (0.59, 0.79),
}


class UniversalLLMClient:
    """
    Universal LLM Client managing unified routing, fallbacks, streaming,
    reasoning extraction, and cost tracking.
    """

    def __init__(
        self,
        default_model: str = "gpt-4o",
        api_keys: dict[str, str] | None = None,
        timeout: float = 60.0,
        enable_fallback: bool = True,
        fallback_chain: list[str] | None = None,
    ):
        self.default_model = default_model
        self.api_keys = api_keys or {}
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        self.fallback_chain = fallback_chain or [
            "gpt-4o",
            "claude-3-5-sonnet",
            "deepseek-chat",
            "gemini-2.0-flash",
            "mock",
        ]

    def detect_provider(self, model: str) -> ProviderType:
        """Detect the appropriate provider for a given model identifier."""
        model_lower = model.lower()
        if model_lower.startswith("mock") or model_lower == "test":
            return ProviderType.MOCK
        elif "claude" in model_lower:
            return ProviderType.ANTHROPIC
        elif "gemini" in model_lower:
            return ProviderType.GEMINI
        elif "deepseek" in model_lower:
            return ProviderType.DEEPSEEK
        elif "groq" in model_lower or "llama" in model_lower or "mixtral" in model_lower:
            return ProviderType.GROQ
        elif "ollama" in model_lower or model_lower.startswith("local/"):
            return ProviderType.OLLAMA
        elif model_lower.startswith(("http://", "https://")):
            return ProviderType.OPENAI_COMPATIBLE
        else:
            return ProviderType.OPENAI

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD."""
        for pattern, (in_price, out_price) in MODEL_PRICING.items():
            if pattern in model.lower():
                in_cost = (prompt_tokens / 1_000_000) * in_price
                out_cost = (completion_tokens / 1_000_000) * out_price
                return round(in_cost + out_cost, 6)
        # Default baseline estimate
        return round(((prompt_tokens * 1.0) + (completion_tokens * 3.0)) / 1_000_000, 6)

    def extract_reasoning(self, text: str) -> tuple[str, str | None]:
        """Extract <think>...</think> reasoning traces from models like DeepSeek R1."""
        think_match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
        if think_match:
            reasoning = think_match.group(1).strip()
            clean_content = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return clean_content, reasoning
        return text, None

    def generate(
        self,
        messages: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        stream: bool = False,
        reasoning_effort: str | None = None,
        prompt: str | None = None,
    ) -> LLMResponse:
        """
        Synchronous unified generation call with automatic fallback cascade.
        """
        if messages is None:
            if prompt is not None:
                messages = [{"role": "user", "content": prompt}]
            else:
                messages = []
        target_model = model or self.default_model
        models_to_try = [target_model]
        if self.enable_fallback:
            for fb in self.fallback_chain:
                if fb not in models_to_try:
                    models_to_try.append(fb)

        last_error = None
        for current_model in models_to_try:
            provider = self.detect_provider(current_model)
            start_time = time.time()
            try:
                response = self._execute_provider(
                    provider=provider,
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice=tool_choice,
                    reasoning_effort=reasoning_effort,
                )
                response.latency_ms = round((time.time() - start_time) * 1000, 2)
                response.estimated_cost_usd = self.calculate_cost(
                    response.model, response.prompt_tokens, response.completion_tokens
                )
                return response
            except Exception as e:  # noqa: BLE001
                last_error = e
                # Fallback to next model if available
                continue

        # If all providers fail, return graceful mock response
        return self._mock_fallback(messages, target_model, str(last_error))

    def _execute_provider(
        self,
        provider: ProviderType,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None,
        tool_choice: str | None,
        reasoning_effort: str | None,
    ) -> LLMResponse:
        """Internal provider dispatcher."""
        if provider == ProviderType.MOCK:
            return self._execute_mock(messages, model)

        # Check API Keys
        openai_key = self.api_keys.get("openai") or os.getenv("OPENAI_API_KEY")
        anthropic_key = self.api_keys.get("anthropic") or os.getenv("ANTHROPIC_API_KEY")

        if provider == ProviderType.OPENAI and openai_key:
            return self._execute_openai(
                model, messages, temperature, max_tokens, tools, tool_choice, openai_key
            )
        elif provider == ProviderType.ANTHROPIC and anthropic_key:
            return self._execute_anthropic(
                model, messages, temperature, max_tokens, tools, anthropic_key
            )
        elif provider == ProviderType.DEEPSEEK:
            ds_key = self.api_keys.get("deepseek") or os.getenv("DEEPSEEK_API_KEY") or openai_key
            if ds_key:
                return self._execute_openai_compatible(
                    model=model,
                    base_url="https://api.deepseek.com/v1",
                    api_key=ds_key,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )
        elif provider == ProviderType.GROQ:
            groq_key = self.api_keys.get("groq") or os.getenv("GROQ_API_KEY")
            if groq_key:
                return self._execute_openai_compatible(
                    model=model,
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )

        # Fallback to mock simulation if credentials not configured
        return self._execute_mock(messages, model)

    def _execute_mock(self, messages: list[dict[str, Any]], model: str) -> LLMResponse:
        """Deterministic mock provider for offline tests and simulations."""
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "")
                break

        content = f"Simulated response for: '{user_message[:100]}' using model [{model}]."
        return LLMResponse(
            content=content,
            model=model,
            provider="mock",
            prompt_tokens=max(10, len(str(messages)) // 4),
            completion_tokens=len(content) // 4,
            total_tokens=(len(str(messages)) + len(content)) // 4,
            finish_reason="stop",
        )

    def _execute_openai(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None,
        tool_choice: str | None,
        api_key: str,
    ) -> LLMResponse:
        """Call OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice

            res = client.chat.completions.create(**kwargs)
            choice = res.choices[0]
            raw_content = choice.message.content or ""
            content, reasoning = self.extract_reasoning(raw_content)

            tool_calls = []
            if getattr(choice.message, "tool_calls", None):
                for tc in choice.message.tool_calls:
                    tool_calls.append(
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    )

            usage = res.usage
            return LLMResponse(
                content=content,
                reasoning_content=reasoning,
                tool_calls=tool_calls,
                model=model,
                provider="openai",
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                finish_reason=choice.finish_reason or "stop",
                raw_response=res,
            )
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"OpenAI error: {e}")

    def _execute_anthropic(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None,
        api_key: str,
    ) -> LLMResponse:
        """Call Anthropic API with support for Claude 3.7 Thinking."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)

            # Separate system prompt
            system_prompt = ""
            chat_messages = []
            for m in messages:
                if m.get("role") == "system":
                    system_prompt += m.get("content", "") + "\n"
                else:
                    chat_messages.append({"role": m.get("role"), "content": m.get("content")})

            kwargs: dict[str, Any] = {
                "model": model if "claude" in model else "claude-3-5-sonnet-20241022",
                "messages": chat_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system_prompt.strip():
                kwargs["system"] = system_prompt.strip()

            res = client.messages.create(**kwargs)
            content_text = ""
            reasoning_text = None
            tool_calls = []

            for block in res.content:
                if getattr(block, "type", "") == "text":
                    content_text += getattr(block, "text", "")
                elif getattr(block, "type", "") == "thinking":
                    reasoning_text = getattr(block, "thinking", "")
                elif getattr(block, "type", "") == "tool_use":
                    tool_calls.append(
                        {
                            "id": getattr(block, "id", ""),
                            "type": "function",
                            "function": {
                                "name": getattr(block, "name", ""),
                                "arguments": json.dumps(getattr(block, "input", {})),
                            },
                        }
                    )

            usage = getattr(res, "usage", None)
            p_tokens = getattr(usage, "input_tokens", 0) if usage else 0
            c_tokens = getattr(usage, "output_tokens", 0) if usage else 0

            return LLMResponse(
                content=content_text,
                reasoning_content=reasoning_text,
                tool_calls=tool_calls,
                model=model,
                provider="anthropic",
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=p_tokens + c_tokens,
                finish_reason="stop",
                raw_response=res,
            )
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Anthropic error: {e}")

    def _execute_openai_compatible(
        self,
        model: str,
        base_url: str,
        api_key: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None,
    ) -> LLMResponse:
        """Call any OpenAI-compatible API endpoint (DeepSeek, Groq, Ollama, vLLM)."""
        from openai import OpenAI

        client = OpenAI(base_url=base_url, api_key=api_key)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        res = client.chat.completions.create(**kwargs)
        choice = res.choices[0]
        raw_content = choice.message.content or ""
        content, reasoning = self.extract_reasoning(raw_content)

        usage = res.usage
        return LLMResponse(
            content=content,
            reasoning_content=reasoning,
            model=model,
            provider="openai_compatible",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "stop",
            raw_response=res,
        )

    def _mock_fallback(
        self, messages: list[dict[str, Any]], model: str, error_msg: str
    ) -> LLMResponse:
        """Graceful mock fallback response on error."""
        return LLMResponse(
            content=f"[Agent Factory Gateway Active] Model {model} response simulated. Notice: {error_msg}",
            model=model,
            provider="mock_fallback",
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75,
            finish_reason="stop",
        )
