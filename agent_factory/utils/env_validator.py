"""
Environment variable validation for Agent Factory.

Validates required and optional environment variables on startup.
"""

import os
from dataclasses import dataclass
from typing import Any

from agent_factory.core.exceptions import ConfigurationError


@dataclass
class EnvVar:
    """Environment variable definition."""

    name: str
    required: bool = False
    default: str | None = None
    description: str = ""
    validator: Any | None = None


class EnvironmentValidationError(ConfigurationError):
    """Raised when environment validation fails."""

    pass


class EnvironmentValidator:
    """
    Validator for application environment variables with support for defaults and strict enforcement.
    """

    def __init__(self):
        self.required_vars: list[tuple[str, str]] = []
        self.optional_vars: dict[str, dict[str, Any]] = {}

    def add_required(self, name: str, description: str = "") -> None:
        """Add a required environment variable."""
        self.required_vars.append((name, description))

    def add_optional(self, name: str, default: str | None = None, description: str = "") -> None:
        """Add an optional environment variable with an optional default value."""
        self.optional_vars[name] = {
            "default": default,
            "description": description,
        }

    def validate(self, raise_on_error: bool = False) -> tuple[bool, list[str]]:
        """
        Validate environment variables.

        Args:
            raise_on_error: If True, raises ConfigurationError on missing required variables.

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors: list[str] = []

        # Check required variables
        for name, description in self.required_vars:
            val = os.getenv(name)
            if not val or not val.strip():
                errors.append(f"Missing required environment variable: {name} ({description})")

        # Populate optional defaults if not set in os.environ
        for name, info in self.optional_vars.items():
            if name not in os.environ and info["default"] is not None:
                os.environ[name] = str(info["default"])

        is_valid = len(errors) == 0
        if not is_valid and raise_on_error:
            raise ConfigurationError(f"Environment validation failed: {', '.join(errors)}")

        return is_valid, errors

    def get(self, name: str, default: str | None = None) -> str | None:
        """Retrieve the value of an environment variable or the provided default."""
        return os.getenv(name, default)


def validate_agent_factory_env(raise_on_error: bool = False) -> EnvironmentValidator:
    """
    Standard environment validator for Agent Factory startup.

    Args:
        raise_on_error: Whether to raise an exception on missing required variables.

    Returns:
        Configured and executed EnvironmentValidator instance.
    """
    validator = EnvironmentValidator()

    # Optional defaults
    validator.add_optional(
        "ENVIRONMENT", "development", "App runtime environment (development, staging, production)"
    )
    validator.add_optional("DATABASE_URL", "sqlite:///agent_factory.db", "Database connection URL")
    validator.add_optional("LOG_LEVEL", "INFO", "Application logging level")
    validator.add_optional(
        "JWT_SECRET", "agent-factory-secret-key-change-in-production", "JWT signing secret"
    )

    # In production, check API keys or database URLs if needed
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        # In strict production mode, enforce credentials if needed
        pass

    validator.validate(raise_on_error=raise_on_error)
    return validator
