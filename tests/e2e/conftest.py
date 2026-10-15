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
    """Create HTTP client for API (live server or in-memory ASGI transport)."""
    configured_url = os.getenv("API_BASE_URL")
    live = configured_url is not None
    if live:
        try:
            with httpx.Client(base_url=api_base_url, timeout=5.0) as probe:
                health = probe.get("/health")
                root = probe.get("/")
            if health.status_code != 200 or root.json().get("name") != "Agent Factory Platform API":
                pytest.fail(f"API_BASE_URL does not point to an Agent Factory API: {api_base_url}")
        except (httpx.HTTPError, ValueError) as exc:
            pytest.fail(f"API_BASE_URL is configured but unavailable: {api_base_url} ({exc})")

    if live:
        client = httpx.Client(
            base_url=api_base_url,
            timeout=30.0,
            follow_redirects=True,
        )
    else:
        from fastapi.testclient import TestClient

        from agent_factory.api.main import app
        from agent_factory.database import init_db

        # TestClient is not used as a context manager here, so initialize the
        # local database explicitly instead of relying on the app lifespan.
        init_db()

        client = TestClient(
            app=app,
            base_url="http://localhost:8000",
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
