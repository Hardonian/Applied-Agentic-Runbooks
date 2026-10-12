"""Live product-path E2E coverage for the authenticated API."""

from uuid import uuid4

import pytest


@pytest.mark.e2e
class TestAuthenticatedProductE2E:
    """Exercise signup and protected agent/workflow management over HTTP."""

    def test_signup_and_manage_product_resources(self, api_client):
        suffix = uuid4().hex
        email = f"release-e2e-{suffix}@example.com"

        unauthenticated = api_client.get("/api/v1/agents/")
        assert unauthenticated.status_code in {401, 403}

        signup = api_client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": "release-e2e-password"},
        )
        assert signup.status_code == 200, signup.text
        token = signup.json()["access_token"]
        api_client.headers["Authorization"] = f"Bearer {token}"

        profile = api_client.get("/api/v1/auth/me")
        assert profile.status_code == 200, profile.text
        assert profile.json()["email"] == email

        agent_id = f"release-e2e-agent-{suffix}"
        create_agent = api_client.post(
            "/api/v1/agents/",
            json={
                "id": agent_id,
                "name": "Release E2E Agent",
                "instructions": "Respond concisely.",
            },
        )
        assert create_agent.status_code == 200, create_agent.text
        assert create_agent.json() == {"id": agent_id, "status": "created"}

        agents = api_client.get("/api/v1/agents/")
        assert agents.status_code == 200, agents.text
        assert agent_id in {agent["id"] for agent in agents.json()}

        workflow_id = f"release-e2e-workflow-{suffix}"
        create_workflow = api_client.post(
            "/api/v1/workflows/",
            json={
                "id": workflow_id,
                "name": "Release E2E Workflow",
                "steps": [{"id": "step-1", "agent_id": agent_id}],
            },
        )
        assert create_workflow.status_code == 200, create_workflow.text
        assert create_workflow.json() == {"id": workflow_id, "status": "created"}

        workflows = api_client.get("/api/v1/workflows/")
        assert workflows.status_code == 200, workflows.text
        assert workflow_id in workflows.json()

        workflow_status = api_client.get(f"/api/v1/workflows/{workflow_id}/status")
        assert workflow_status.status_code == 200, workflow_status.text
        assert workflow_status.json()["workflow_id"] == workflow_id
