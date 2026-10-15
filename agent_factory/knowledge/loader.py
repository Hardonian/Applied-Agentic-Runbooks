"""
Load knowledge packs from YAML/JSON files.
"""

from pathlib import Path

import yaml

from agent_factory.knowledge.model import (
    DataSource,
    EmbeddingConfig,
    KnowledgePack,
    RetrieverConfig,
)


class KnowledgePackLoader:
    """Load knowledge packs from files."""
    
    def load(self, pack_path: str) -> KnowledgePack:
        """
        Load knowledge pack from YAML file.
        
        Args:
            pack_path: Path to pack.yaml file
        
        Returns:
            Loaded KnowledgePack
        """
        pack_path = Path(pack_path)
        if not pack_path.exists():
            raise FileNotFoundError(f"Knowledge pack not found: {pack_path}")
        
        with open(pack_path, "r") as f:
            data = yaml.safe_load(f)
        
        pack_data = data.get("knowledge_pack", {})
        
        # Parse data sources
        data_sources = []
        for ds_data in pack_data.get("data_sources", []):
            data_sources.append(DataSource(
                type=ds_data.get("type", "directory"),
                path=ds_data.get("path"),
                url=ds_data.get("url"),
                config=ds_data.get("config", {}),
            ))
        
        # Parse embedding config
        emb_data = pack_data.get("embedding_config", {})
        embedding_config = EmbeddingConfig(
            model=emb_data.get("model", "text-embedding-3-small"),
            provider=emb_data.get("provider", "openai"),
            chunk_size=emb_data.get("chunk_size", 1000),
            chunk_overlap=emb_data.get("chunk_overlap", 200),
            config=emb_data.get("config", {}),
        )
        
        # Parse retriever config
        ret_data = pack_data.get("retriever_config", {})
        retriever_config = RetrieverConfig(
            type=ret_data.get("type", "vector_store"),
            vector_store=ret_data.get("vector_store", "chroma"),
            top_k=ret_data.get("top_k", 5),
            similarity_threshold=ret_data.get("similarity_threshold", 0.7),
            config=ret_data.get("config", {}),
        )
        
        return KnowledgePack(
            id=pack_data.get("id", ""),
            name=pack_data.get("name", ""),
            version=pack_data.get("version", "1.0.0"),
            description=pack_data.get("description", ""),
            domain=pack_data.get("domain", "general"),
            tags=pack_data.get("tags", []),
            data_sources=data_sources,
            embedding_config=embedding_config,
            retriever_config=retriever_config,
            metadata=pack_data.get("metadata", {}),
        )
