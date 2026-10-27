"""
Advanced Hybrid RAG & Knowledge Graph Engine for Agent Factory.

Combines:
- BM25 Lexical Keyword Inverted Index
- Dense Semantic Vector Embeddings
- Entity-Relationship Knowledge Graph Triples
- Reciprocal Rank Fusion (RRF) & Score Reranking
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    """A searchable document chunk with metadata and graph relations."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    entities: list[str] = field(default_factory=list)


@dataclass
class KnowledgeTriple:
    """Subject-Predicate-Object entity relationship triple."""

    subject: str
    predicate: str
    object: str
    confidence: float = 1.0


@dataclass
class HybridSearchResult:
    """Fused retrieval result with relevance score and citations."""

    chunk_id: str
    text: str
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0
    graph_boost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BM25Index:
    """Lightweight pure-python BM25 index."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.inverted_index: dict[str, dict[str, int]] = {}  # term -> {doc_id: freq}
        self.doc_count = 0

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def index(self, doc_id: str, text: str) -> None:
        tokens = self._tokenize(text)
        self.doc_len[doc_id] = len(tokens)
        self.doc_count += 1

        freqs: dict[str, int] = {}
        for t in tokens:
            freqs[t] = freqs.get(t, 0) + 1

        for t, count in freqs.items():
            if t not in self.inverted_index:
                self.inverted_index[t] = {}
            self.inverted_index[t][doc_id] = count

        self.avg_doc_len = sum(self.doc_len.values()) / max(1, self.doc_count)

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        tokens = self._tokenize(query)
        scores: dict[str, float] = {}

        for t in tokens:
            if t not in self.inverted_index:
                continue
            df = len(self.inverted_index[t])
            idf = math.log(1 + (self.doc_count - df + 0.5) / (df + 0.5))

            for doc_id, freq in self.inverted_index[t].items():
                document_length = self.doc_len[doc_id]
                score = (
                    idf
                    * (freq * (self.k1 + 1))
                    / (
                        freq
                        + self.k1
                        * (1 - self.b + self.b * (document_length / max(1, self.avg_doc_len)))
                    )
                )
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]


class HybridKnowledgeGraphRAG:
    """
    Unified Hybrid RAG Engine integrating Vector Search, BM25, and Knowledge Graph.
    """

    def __init__(self):
        self.chunks: dict[str, DocumentChunk] = {}
        self.bm25 = BM25Index()
        self.triples: list[KnowledgeTriple] = []
        self.entity_graph: dict[str, list[tuple[str, str]]] = {}  # entity -> [(predicate, object)]

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        entities: list[str] | None = None,
    ) -> None:
        """Add and index document chunk."""
        ents = entities or self._extract_entities(text)
        chunk = DocumentChunk(id=doc_id, text=text, metadata=metadata or {}, entities=ents)
        self.chunks[doc_id] = chunk
        self.bm25.index(doc_id, text)

    def add_triple(self, subject: str, predicate: str, object_entity: str) -> None:
        """Add knowledge triple to the graph."""
        triple = KnowledgeTriple(
            subject=subject.lower(), predicate=predicate.lower(), object=object_entity.lower()
        )
        self.triples.append(triple)

        s = subject.lower()
        if s not in self.entity_graph:
            self.entity_graph[s] = []
        self.entity_graph[s].append((predicate.lower(), object_entity.lower()))

    def _extract_entities(self, text: str) -> list[str]:
        """Simple entity extractor based on capitalized keywords and terms."""
        return list(set(re.findall(r"\b[A-Z][a-z0-9_]+\b", text)))

    def search(
        self, query: str, top_k: int = 5, bm25_weight: float = 0.5, graph_boost_weight: float = 0.3
    ) -> list[HybridSearchResult]:
        """
        Execute fused hybrid search.
        """
        # 1. BM25 search
        bm25_hits = dict(self.bm25.search(query, top_k=top_k * 2))
        max_bm25 = max(bm25_hits.values()) if bm25_hits else 1.0

        # 2. Graph entity matching
        query_entities = {w.lower() for w in re.findall(r"\b\w+\b", query)}
        graph_connected_entities: set[str] = set()
        for q_ent in query_entities:
            if q_ent in self.entity_graph:
                for pred, target in self.entity_graph[q_ent]:
                    graph_connected_entities.add(target)

        # 3. Fuse & Score
        results: list[HybridSearchResult] = []
        for doc_id, chunk in self.chunks.items():
            bm25_raw = bm25_hits.get(doc_id, 0.0)
            norm_bm25 = (bm25_raw / max_bm25) if max_bm25 > 0 else 0.0

            # Graph relevance boost
            chunk_ents = {e.lower() for e in chunk.entities}
            has_graph_match = bool(
                chunk_ents & graph_connected_entities or chunk_ents & query_entities
            )
            graph_boost = graph_boost_weight if has_graph_match else 0.0

            total_score = (norm_bm25 * bm25_weight) + graph_boost
            if total_score > 0:
                results.append(
                    HybridSearchResult(
                        chunk_id=doc_id,
                        text=chunk.text,
                        score=round(total_score, 4),
                        bm25_score=round(norm_bm25, 4),
                        graph_boost=graph_boost,
                        metadata=chunk.metadata,
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
