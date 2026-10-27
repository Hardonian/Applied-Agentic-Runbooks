"""Integration tests for API with database."""

import pytest
from fastapi.testclient import TestClient

from agent_factory.api.main import app


@pytest.mark.integration
def test_api_health_check():
    """Test API health check endpoint."""
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code in [200, 503]  # May be degraded if DB unavailable
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_api_root():
    """Test API root endpoint."""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


@pytest.mark.integration
def test_api_liveness():
    """Test API liveness probe."""
    client = TestClient(app)

    response = client.get("/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
