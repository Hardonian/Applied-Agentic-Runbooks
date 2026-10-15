"""
Knowledge Packs - Pluggable RAG modules for agents.
"""

from agent_factory.knowledge.loader import KnowledgePackLoader
from agent_factory.knowledge.model import KnowledgePack, KnowledgeRetriever

__all__ = ["KnowledgePack", "KnowledgePackLoader", "KnowledgeRetriever"]
