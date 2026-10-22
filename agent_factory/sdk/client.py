"""
Python SDK client for Agent Factory Platform API.
"""

import os
from typing import Any

import httpx


class Client:
    """
    Python SDK client for Agent Factory Platform.

    Provides programmatic access to agents, workflows, blueprints, and telemetry.

    Example:
        >>> client = Client(api_key="your-api-key")
        >>> result = client.run_agent("my-agent", "Hello!")
        >>> blueprints = client.list_blueprints()
        >>> client.install_blueprint("student-support-assistant")
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize SDK client.

        Args:
            api_key: API key for authentication (defaults to AGENT_FACTORY_API_KEY env var)
            base_url: Base URL for API (defaults to AGENT_FACTORY_API_URL env var or localhost)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("AGENT_FACTORY_API_KEY")
        self.base_url = base_url or os.getenv("AGENT_FACTORY_API_URL", "http://localhost:8000")
        self.timeout = timeout

        # Remove trailing slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        # Setup HTTP client
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request.

        Args:
            method: HTTP method
            path: API path
            json: JSON body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        response = self.client.request(method, path, json=json, params=params)
        response.raise_for_status()
        return response.json()

    # Agent methods

    def create_agent(
        self,
        agent_id: str,
        name: str,
        instructions: str,
        model: str = "gpt-4o",
    ) -> dict[str, Any]:
        """
        Create a new agent.

        Args:
            agent_id: Unique agent ID
            name: Agent name
            instructions: Agent instructions
            model: Model to use

        Returns:
            Created agent info
        """
        return self._request(
            "POST",
            "/api/v1/agents/",
            json={
                "id": agent_id,
                "name": name,
                "instructions": instructions,
                "model": model,
            },
        )

    def list_agents(self) -> list[dict[str, Any]]:
        """
        List all agents.

        Returns:
            List of agents
        """
        return self._request("GET", "/api/v1/agents/")

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        """
        Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent info
        """
        return self._request("GET", f"/api/v1/agents/{agent_id}")

    def run_agent(
        self,
        agent_id: str,
        input_text: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an agent.

        Args:
            agent_id: Agent ID
            input_text: Input text
            session_id: Optional session ID
            context: Optional context

        Returns:
            Agent execution result
        """
        return self._request(
            "POST",
            f"/api/v1/agents/{agent_id}/run",
            json={
                "input_text": input_text,
                "session_id": session_id,
                "context": context,
            },
        )

    def delete_agent(self, agent_id: str) -> dict[str, Any]:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Deletion status
        """
        return self._request("DELETE", f"/api/v1/agents/{agent_id}")

    # Workflow methods

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        definition: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a new workflow.

        Args:
            workflow_id: Unique workflow ID
            name: Workflow name
            definition: Workflow definition

        Returns:
            Created workflow info
        """
        return self._request(
            "POST",
            "/api/v1/workflows/",
            json={
                "id": workflow_id,
                "name": name,
                "definition": definition,
            },
        )

    def list_workflows(self) -> list[dict[str, Any]]:
        """
        List all workflows.

        Returns:
            List of workflows
        """
        return self._request("GET", "/api/v1/workflows/")

    def run_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run a workflow.

        Args:
            workflow_id: Workflow ID
            context: Initial context

        Returns:
            Workflow execution result
        """
        return self._request(
            "POST",
            f"/api/v1/workflows/{workflow_id}/run",
            json={"context": context},
        )

    # Blueprint methods

    def list_blueprints(self) -> list[dict[str, Any]]:
        """
        List available blueprints.

        Returns:
            List of blueprints
        """
        return self._request("GET", "/api/v1/blueprints/")

    def get_blueprint(self, blueprint_id: str) -> dict[str, Any]:
        """
        Get blueprint by ID.

        Args:
            blueprint_id: Blueprint ID

        Returns:
            Blueprint info
        """
        return self._request("GET", f"/api/v1/blueprints/{blueprint_id}")

    def install_blueprint(
        self,
        blueprint_id: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Install a blueprint.

        Args:
            blueprint_id: Blueprint ID
            project_id: Optional project ID

        Returns:
            Installation result
        """
        return self._request(
            "POST",
            f"/api/v1/blueprints/{blueprint_id}/install",
            json={"project_id": project_id} if project_id else None,
        )

    def search_blueprints(self, query: str) -> list[dict[str, Any]]:
        """
        Search blueprints.

        Args:
            query: Search query

        Returns:
            List of matching blueprints
        """
        return self._request("GET", "/api/v1/blueprints/search", params={"q": query})

    # Telemetry/Metrics methods

    def get_metrics(
        self,
        tenant_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Get metrics summary.

        Args:
            tenant_id: Optional tenant ID filter
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Metrics summary
        """
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._request("GET", "/api/v1/telemetry/metrics", params=params)

    def get_tenant_metrics(self, tenant_id: str) -> dict[str, Any]:
        """
        Get metrics for a specific tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant metrics
        """
        return self._request("GET", f"/api/v1/telemetry/metrics/tenant/{tenant_id}")

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
