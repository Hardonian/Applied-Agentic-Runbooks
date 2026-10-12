"""Authorization tests for referral routes."""

from fastapi.testclient import TestClient

from agent_factory.api.main import app
from agent_factory.security.auth import User, get_current_user


def test_referral_codes_are_bound_to_the_authenticated_owner():
    app.dependency_overrides[get_current_user] = lambda: User(
        id="owner", email="owner@example.test", roles=["user"], tenant_id="tenant-1"
    )
    try:
        client = TestClient(app)
        generated = client.post("/api/v1/referrals/generate")
        assert generated.status_code == 200
        code = generated.json()["referral_code"]

        app.dependency_overrides[get_current_user] = lambda: User(
            id="other", email="other@example.test", roles=["user"], tenant_id="tenant-2"
        )
        denied = client.post("/api/v1/referrals/send", json={"referral_code": code})
        assert denied.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
