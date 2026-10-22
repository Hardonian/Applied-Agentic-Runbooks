"""E2E test configuration."""

import os
from collections.abc import Generator

import httpx
import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_client(api_base_url: str) -> Generator[httpx.Client, None, None]:
    """Create HTTP client for API."""
    client = httpx.Client(
        base_url=api_base_url,
        timeout=30.0,
        follow_redirects=True,
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def api_key() -> str:
    """Get API key from environment."""
    key = os.getenv("API_KEY", "")
    if not key:
        pytest.skip("API_KEY not set")
    return key


@pytest.fixture(scope="session")
def authenticated_client(api_base_url: str, api_key: str) -> Generator[httpx.Client, None, None]:
    """Create authenticated HTTP client."""
    client = httpx.Client(
        base_url=api_base_url,
        timeout=30.0,
        follow_redirects=True,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    yield client
    client.close()
