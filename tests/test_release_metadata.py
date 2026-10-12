"""Release metadata and public version contract tests."""

import asyncio

from agent_factory import __version__
from agent_factory.api.main import app, health, root


def test_api_version_uses_package_version():
    assert app.version == __version__
    assert root()["version"] == __version__


def test_health_version_uses_package_version():
    response = asyncio.run(health())
    assert response.status_code == 200
    assert __version__.encode() in response.body
