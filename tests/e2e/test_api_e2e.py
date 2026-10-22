"""End-to-end API tests."""

import time

import httpx
import pytest


@pytest.mark.e2e
class TestAPIE2E:
    """End-to-end API tests."""

    def test_health_check(self, api_client: httpx.Client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "checks" in data
        assert "database" in data["checks"]

    def test_readiness(self, api_client: httpx.Client):
        """Test readiness endpoint."""
        response = api_client.get("/ready")
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready"

    def test_liveness(self, api_client: httpx.Client):
        """Test liveness endpoint."""
        response = api_client.get("/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"

    def test_api_docs(self, api_client: httpx.Client):
        """Test API documentation endpoint."""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_schema(self, api_client: httpx.Client):
        """Test OpenAPI schema endpoint."""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_agents_endpoint(self, api_client: httpx.Client):
        """Test agents endpoint."""
        response = api_client.get("/api/v1/agents")
        # May require auth, so 200, 401, or 403 are all valid
        assert response.status_code in [200, 401, 403]

    def test_workflows_endpoint(self, api_client: httpx.Client):
        """Test workflows endpoint."""
        response = api_client.get("/api/v1/workflows")
        assert response.status_code in [200, 401, 403]

    def test_blueprints_endpoint(self, api_client: httpx.Client):
        """Test blueprints endpoint."""
        response = api_client.get("/api/v1/blueprints")
        assert response.status_code in [200, 401, 403]

    def test_metrics_endpoint(self, api_client: httpx.Client):
        """Test metrics endpoint."""
        response = api_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

        # Check for Prometheus metrics format
        content = response.text
        assert "http_requests_total" in content or "# HELP" in content


@pytest.mark.e2e
class TestAgentE2E:
    """End-to-end agent tests."""

    def test_create_and_run_agent(self, authenticated_client: httpx.Client):
        """Test creating and running an agent."""
        # Create agent
        agent_data = {
            "id": f"e2e-test-agent-{int(time.time())}",
            "name": "E2E Test Agent",
            "instructions": "You are a helpful test assistant.",
        }

        response = authenticated_client.post("/api/v1/agents", json=agent_data)
        # May fail if auth not configured, skip if so
        if response.status_code == 401:
            pytest.skip("Authentication not configured for E2E tests")

        assert response.status_code in [200, 201]

        # Run agent
        run_data = {"input": "Hello, this is a test!"}
        agent_id = agent_data["id"]

        response = authenticated_client.post(f"/api/v1/agents/{agent_id}/run", json=run_data)

        if response.status_code == 200:
            result = response.json()
            assert "output" in result or "response" in result


@pytest.mark.e2e
class TestWorkflowE2E:
    """End-to-end workflow tests."""

    def test_workflow_endpoints(self, authenticated_client: httpx.Client):
        """Test workflow endpoints."""
        # List workflows
        response = authenticated_client.get("/api/v1/workflows")
        if response.status_code == 401:
            pytest.skip("Authentication not configured")

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            workflows = response.json()
            assert isinstance(workflows, (list, dict))


@pytest.mark.e2e
class TestPerformanceE2E:
    """Performance and load tests."""

    def test_response_time(self, api_client: httpx.Client):
        """Test API response time."""
        start = time.time()
        response = api_client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0, f"Health check took {duration:.2f}s (should be < 2s)"

    def test_concurrent_requests(self, api_client: httpx.Client):
        """Test concurrent request handling."""
        import concurrent.futures

        def make_request():
            return api_client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        assert all(r.status_code == 200 for r in results)
