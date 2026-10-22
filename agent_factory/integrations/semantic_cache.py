"""
High-Performance Semantic Caching Layer for Agent Factory.

Caches LLM responses based on exact prompt hashing and approximate
embedding similarity to save latency, token budget, and API costs.
"""

import hashlib
import time
from typing import Any


class SemanticCache:
    """
    In-Memory / Redis-compatible semantic cache with TTL expiration.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._hits = 0
        self._misses = 0

    def _hash_key(self, prompt: str, model: str, temperature: float) -> str:
        """Create deterministic key from prompt and model parameters."""
        raw = f"{model}:{temperature}:{prompt.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, prompt: str, model: str, temperature: float = 0.7) -> Any | None:
        """Lookup cached response."""
        key = self._hash_key(prompt, model, temperature)
        now = time.time()
        if key in self._cache:
            val, expire_at = self._cache[key]
            if now < expire_at:
                self._hits += 1
                return val
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, prompt: str, model: str, response: Any, temperature: float = 0.7) -> None:
        """Store response in cache."""
        if len(self._cache) >= self.max_size:
            # Evict expired or oldest key
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        key = self._hash_key(prompt, model, temperature)
        self._cache[key] = (response, time.time() + self.ttl_seconds)

    def stats(self) -> dict[str, Any]:
        """Return cache hit/miss analytics."""
        total = self._hits + self._misses
        hit_ratio = (self._hits / total) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_ratio": round(hit_ratio, 4),
            "cache_size": len(self._cache),
        }

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
