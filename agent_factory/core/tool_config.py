"""
Tool configuration schema.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolConfig:
    """Configuration for a Tool."""

    timeout: int = 30  # seconds
    retry_attempts: int = 3
    rate_limit: int | None = None  # requests per minute
    cache_enabled: bool = False
    cache_ttl: int = 3600  # seconds
    require_auth: bool = False
    auth_config: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
