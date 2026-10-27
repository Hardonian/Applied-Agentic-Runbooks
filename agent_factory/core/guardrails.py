"""
Guardrails for agent safety and validation.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class GuardrailResult:
    """Result from guardrail validation."""

    allowed: bool
    reason: str | None = None
    modified_output: str | None = None
    metadata: dict[str, Any] | None = None


class Guardrail(ABC):
    """Abstract base class for guardrails."""

    @abstractmethod
    def check(self, text: str) -> GuardrailResult:
        """Check if text passes the guardrail."""


class Guardrails:
    """
    Collection of guardrails for agent safety.

    Example:
        >>> guardrails = Guardrails()
        >>> guardrails.add_guardrail(ProfanityGuardrail())
        >>> result = guardrails.validate_input("Hello")
        >>> assert result.allowed
    """

    def __init__(self):
        """Initialize guardrails collection."""
        self.input_guardrails: list[Guardrail] = []
        self.output_guardrails: list[Guardrail] = []

    def add_input_guardrail(self, guardrail: Guardrail) -> None:
        """Add a guardrail for input validation."""
        self.input_guardrails.append(guardrail)

    def add_output_guardrail(self, guardrail: Guardrail) -> None:
        """Add a guardrail for output validation."""
        self.output_guardrails.append(guardrail)

    def validate_input(self, text: str) -> GuardrailResult:
        """
        Validate input text against all input guardrails.

        Args:
            text: Input text to validate

        Returns:
            GuardrailResult indicating if input is allowed
        """
        for guardrail in self.input_guardrails:
            result = guardrail.check(text)
            if not result.allowed:
                return result

        return GuardrailResult(allowed=True)

    def validate_output(self, text: str) -> GuardrailResult:
        """
        Validate output text against all output guardrails.

        Args:
            text: Output text to validate

        Returns:
            GuardrailResult indicating if output is allowed
        """
        modified_text = text

        for guardrail in self.output_guardrails:
            result = guardrail.check(modified_text)
            if not result.allowed:
                if result.modified_output:
                    modified_text = result.modified_output
                else:
                    return result

        if modified_text != text:
            return GuardrailResult(
                allowed=True,
                modified_output=modified_text,
                reason="Output was modified by guardrails",
            )

        return GuardrailResult(allowed=True)


class ProfanityGuardrail(Guardrail):
    """Guardrail to detect and block profanity."""

    def __init__(self, profanity_list: list[str] | None = None):
        """
        Initialize profanity guardrail.

        Args:
            profanity_list: Optional list of profane words (uses default if None)
        """
        self.profanity_list = profanity_list or [
            # Add common profanity words here (keeping it minimal for example)
        ]

    def check(self, text: str) -> GuardrailResult:
        """Check for profanity."""
        text_lower = text.lower()

        for word in self.profanity_list:
            if word.lower() in text_lower:
                return GuardrailResult(
                    allowed=False,
                    reason=f"Profanity detected: {word}",
                )

        return GuardrailResult(allowed=True)


class SQLInjectionGuardrail(Guardrail):
    """Guardrail to detect SQL injection attempts."""

    def __init__(self):
        """Initialize SQL injection guardrail."""
        self.sql_keywords = [
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "EXEC",
            "EXECUTE",
            "UNION",
            "SCRIPT",
        ]
        self.sql_patterns = [
            r"';.*--",
            r"';.*;",
            r"OR\s+1\s*=\s*1",
            r"UNION\s+SELECT",
        ]

    def check(self, text: str) -> GuardrailResult:
        """Check for SQL injection patterns."""
        text_upper = text.upper()

        # Check for SQL keywords in suspicious contexts
        for keyword in self.sql_keywords:
            if keyword in text_upper:
                # Check if it's part of a SQL injection pattern
                for pattern in self.sql_patterns:
                    if re.search(pattern, text_upper, re.IGNORECASE):
                        return GuardrailResult(
                            allowed=False,
                            reason="Potential SQL injection detected",
                        )

        return GuardrailResult(allowed=True)


class LengthGuardrail(Guardrail):
    """Guardrail to enforce length limits."""

    def __init__(self, max_length: int = 10000, min_length: int = 0):
        """
        Initialize length guardrail.

        Args:
            max_length: Maximum allowed length
            min_length: Minimum allowed length
        """
        self.max_length = max_length
        self.min_length = min_length

    def check(self, text: str) -> GuardrailResult:
        """Check text length."""
        length = len(text)

        if length > self.max_length:
            return GuardrailResult(
                allowed=False,
                reason=f"Text exceeds maximum length: {length} > {self.max_length}",
            )

        if length < self.min_length:
            return GuardrailResult(
                allowed=False,
                reason=f"Text below minimum length: {length} < {self.min_length}",
            )

        return GuardrailResult(allowed=True)


class PIIGuardrail(Guardrail):
    """Guardrail to detect Personally Identifiable Information."""

    def __init__(self):
        """Initialize PII guardrail."""
        # Email pattern
        self.email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        # Credit card pattern (simplified)
        self.cc_pattern = r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
        # SSN pattern (US)
        self.ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"

    def check(self, text: str) -> GuardrailResult:
        """Check for PII."""
        if re.search(self.email_pattern, text):
            return GuardrailResult(
                allowed=False,
                reason="Email address detected in text",
            )

        if re.search(self.cc_pattern, text):
            return GuardrailResult(
                allowed=False,
                reason="Credit card number detected in text",
            )

        if re.search(self.ssn_pattern, text):
            return GuardrailResult(
                allowed=False,
                reason="SSN detected in text",
            )

        return GuardrailResult(allowed=True)
