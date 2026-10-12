"""
Environment variable validation for Agent Factory.

Validates required and optional environment variables on startup.
"""

import os
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from agent_factory.core.exceptions import ConfigurationError


@dataclass
class EnvVar:
    """Environment variable definition."""
    name: str
    required: bool = False
    default: Optional[str] = None
    description: str = ""
    validator: Optional[Any] = None


class EnvironmentValidationError(ConfigurationError):
    """Raised when environment validation fails."""
    pass


class EnvironmentValidator:
    """
    Validator for application environment variables with support for defaults and strict enforcement.
    """

    def __init__(self):
        self.required_vars: List[Tuple[str, str]] = []
        self.optional_vars: Dict[str, Dict[str, Any]] = {}

    def add_required(self, name: str, description: str = "") -> None:
        """Add a required environment variable."""
        self.required_vars.append((name, description))

    def add_optional(self, name: str, default: Optional[str] = None, description: str = "") -> None:
        """Add an optional environment variable with an optional default value."""
        self.optional_vars[name] = {
            "default": default,
            "description": description,
        }

    def validate(self, raise_on_error: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate environment variables.
        
        Args:
            raise_on_error: If True, raises ConfigurationError on missing required variables.
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors: List[str] = []

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

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
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
    validator.add_optional("ENVIRONMENT", "development", "App runtime environment (development, staging, production)")
    validator.add_optional("DATABASE_URL", "sqlite:///agent_factory.db", "Database connection URL")
    validator.add_optional("LOG_LEVEL", "INFO", "Application logging level")
    validator.add_optional(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080",
        "Comma-separated browser origins allowed to call the API",
    )

    is_valid, errors = validator.validate(raise_on_error=False)
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in {"development", "staging", "production", "test"}:
        errors.append("ENVIRONMENT must be development, staging, production, or test")

    if env == "production":
        secret = os.getenv("JWT_SECRET_KEY", "")
        insecure_secrets = {
            "",
            "your-secret-key-change-in-production",
            "agent-factory-secret-key-change-in-production",
        }
        if secret in insecure_secrets or len(secret) < 32:
            errors.append("JWT_SECRET_KEY must be a unique secret of at least 32 characters in production")
        if not os.getenv("DATABASE_URL"):
            errors.append("Missing required environment variable: DATABASE_URL (production database connection)")
        cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
        if not cors_origins or "*" in cors_origins:
            errors.append("CORS_ORIGINS must list explicit origins in production")
        elif any(urlparse(origin).scheme not in {"http", "https"} or not urlparse(origin).netloc for origin in cors_origins):
            errors.append("CORS_ORIGINS contains an invalid origin")
        if os.getenv("DEBUG", "false").lower() == "true":
            errors.append("DEBUG must be false in production")

    if errors and raise_on_error:
        raise ConfigurationError(f"Environment validation failed: {', '.join(errors)}")
    return validator
