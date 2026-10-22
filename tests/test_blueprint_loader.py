"""Tests for Blueprint Loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from agent_factory.blueprints.loader import BlueprintLoader


@pytest.mark.unit
def test_load_blueprint():
    """Test loading a blueprint from YAML."""
    loader = BlueprintLoader()

    # Create temporary blueprint file
    blueprint_data = {
        "blueprint": {
            "id": "test-blueprint",
            "name": "Test Blueprint",
            "version": "1.0.0",
            "description": "A test blueprint",
            "author": "Test Author",
            "category": "test",
            "tags": ["test"],
            "agents": [],
            "tools": [],
            "workflows": [],
            "knowledge_packs": [],
            "config": {
                "dependencies": [],
                "environment_variables": {},
                "required_tools": [],
                "required_agents": [],
            },
            "metadata": {
                "demo_url": "",
                "documentation": "",
            },
            "pricing": {
                "model": "free",
                "price": 0.0,
                "currency": "USD",
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        blueprint_path = Path(tmpdir) / "blueprint.yaml"
        blueprint_path.write_text(yaml.dump(blueprint_data))

        blueprint = loader.load(str(blueprint_path))

        assert blueprint.id == "test-blueprint"
        assert blueprint.name == "Test Blueprint"
        assert blueprint.version == "1.0.0"
        assert blueprint.author == "Test Author"


@pytest.mark.unit
def test_load_blueprint_not_found():
    """Test loading non-existent blueprint."""
    loader = BlueprintLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("non-existent.yaml")
