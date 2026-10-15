"""Tests for Knowledge Pack Loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from agent_factory.knowledge.loader import KnowledgePackLoader


@pytest.mark.unit
def test_load_knowledge_pack():
    """Test loading a knowledge pack from YAML."""
    loader = KnowledgePackLoader()
    
    # Create temporary pack file
    pack_data = {
        "knowledge_pack": {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "description": "A test knowledge pack",
            "domain": "test",
            "tags": ["test"],
            "data_sources": [
                {
                    "type": "directory",
                    "path": "./data",
                }
            ],
            "embedding_config": {
                "model": "text-embedding-3-small",
                "provider": "openai",
                "chunk_size": 1000,
                "chunk_overlap": 200,
            },
            "retriever_config": {
                "type": "vector_store",
                "vector_store": "chroma",
                "top_k": 5,
                "similarity_threshold": 0.7,
            },
            "metadata": {},
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_path = Path(tmpdir) / "pack.yaml"
        pack_path.write_text(yaml.dump(pack_data))
        
        pack = loader.load(str(pack_path))
        
        assert pack.id == "test-pack"
        assert pack.name == "Test Pack"
        assert pack.version == "1.0.0"
        assert len(pack.data_sources) == 1


@pytest.mark.unit
def test_load_knowledge_pack_not_found():
    """Test loading non-existent knowledge pack."""
    loader = KnowledgePackLoader()
    
    with pytest.raises(FileNotFoundError):
        loader.load("non-existent.yaml")
