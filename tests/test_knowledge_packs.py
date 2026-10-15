"""
Tests for knowledge packs.
"""

import yaml

from agent_factory.knowledge import KnowledgePackLoader
from agent_factory.knowledge.model import (
    DataSource,
    EmbeddingConfig,
    KnowledgePack,
    RetrieverConfig,
)


def test_knowledge_pack_model():
    """Test knowledge pack model."""
    pack = KnowledgePack(
        id="test-pack",
        name="Test Pack",
        version="1.0.0",
        description="Test description",
        domain="test",
        data_sources=[
            DataSource(type="directory", path="./data"),
        ],
        embedding_config=EmbeddingConfig(
            model="text-embedding-3-small",
            provider="openai",
        ),
        retriever_config=RetrieverConfig(
            type="vector_store",
            vector_store="chroma",
        ),
    )
    
    assert pack.id == "test-pack"
    assert pack.domain == "test"
    assert len(pack.data_sources) == 1


def test_knowledge_pack_loader(tmp_path):
    """Test knowledge pack loader."""
    # Create test pack YAML
    pack_data = {
        "knowledge_pack": {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "Test",
            "domain": "test",
            "tags": ["test"],
            "data_sources": [
                {
                    "type": "directory",
                    "path": "./data",
                },
            ],
            "embedding_config": {
                "model": "text-embedding-3-small",
                "provider": "openai",
            },
            "retriever_config": {
                "type": "vector_store",
                "vector_store": "chroma",
            },
        },
    }
    
    pack_path = tmp_path / "pack.yaml"
    with open(pack_path, "w") as f:
        yaml.dump(pack_data, f)
    
    # Load
    loader = KnowledgePackLoader()
    pack = loader.load(str(pack_path))
    
    assert pack.id == "test-pack"
    assert pack.name == "Test Pack"
    assert len(pack.data_sources) == 1
