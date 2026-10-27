"""Configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Configuration manager for Agent Factory Platform."""

    def __init__(self, env_file: str | None = None):
        """
        Initialize configuration.

        Args:
            env_file: Optional path to .env file
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try common locations
            for path in [".env", "~/.agent_factory/.env"]:
                env_path = Path(path).expanduser()
                if env_path.exists():
                    load_dotenv(env_path)
                    break

    @property
    def openai_api_key(self) -> str | None:
        """Get OpenAI API key."""
        return os.getenv("OPENAI_API_KEY")

    @property
    def anthropic_api_key(self) -> str | None:
        """Get Anthropic API key."""
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def environment(self) -> str:
        """Get environment (development, production, etc.)."""
        return os.getenv("ENVIRONMENT", "development")

    @property
    def registry_path(self) -> str:
        """Get registry path."""
        return os.getenv("AGENT_FACTORY_REGISTRY_PATH", "~/.agent_factory")

    @property
    def api_base_url(self) -> str:
        """Get API base URL."""
        return os.getenv("AGENT_FACTORY_API_URL", "https://api.agentfactory.io")
