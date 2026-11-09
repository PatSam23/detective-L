"""
Semantic Vector Cache for LLM Gateway.

Upgrades the existing Redis hash-based cache to also support
semantic similarity matching using ChromaDB + all-MiniLM-L6-v2 embeddings.

Flow:
  1. Exact hash match (Redis) → instant hit
  2. Semantic match (ChromaDB, cosine similarity ≥ threshold) → semantic hit
  3. Miss → call LLM provider → store in both Redis + ChromaDB

This means paraphrased queries ("M3 MacBook vs Vivobook" and
"MacBook Air M3 compared to ASUS Vivobook") both get cache hits.
"""

import hashlib
import json
import logging
import os
from typing import Optional, Dict, Any, List, Tuple

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger("semantic_cache")

# Default similarity threshold (0.0–1.0, higher = stricter matching)
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.90"))

# Persist ChromaDB to disk so it survives restarts
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data"),
)
COLLECTION_NAME = "llm_semantic_cache"


def _extract_text_for_embedding(messages: List[dict]) -> str:
    """
    Build a single string to embed from a list of chat messages.
    Concatenates all user/human messages (the prompt content).
    System messages are excluded — they're boilerplate, not query intent.
    """
    parts = [
        m["content"]
        for m in messages
        if m.get("role") in ("user", "human") and m.get("content")
    ]
    return " ".join(parts).strip()


def _make_exact_key(provider: str, model: str, messages: List[dict]) -> str:
    """SHA256 key — identical to the one used by the existing Redis CacheManager."""
    messages_str = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    content = f"{provider}:{model}:{messages_str}"
    return hashlib.sha256(content.encode()).hexdigest()


class SemanticCacheManager:
    """
    Wraps ChromaDB to provide semantic similarity-based cache lookups.

    Usage:
        cache = SemanticCacheManager()
        result = cache.get(provider, model, messages)   # None if miss
        cache.set(provider, model, messages, response_dict)
    """

    def __init__(
        self,
        persist_dir: str = CHROMA_PERSIST_DIR,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        enabled: bool = True,
    ):
        self.threshold = similarity_threshold
        self.enabled = enabled
        self.stats = {"semantic_hits": 0, "misses": 0, "errors": 0}
        self.collection = None
        self._ef = None

        if not self.enabled:
            return

        try:
            os.makedirs(persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_dir)
            # all-MiniLM-L6-v2: 384-dim, runs locally via ONNX — no API calls
            self._ef = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"SemanticCacheManager ready — threshold={self.threshold}, "
                f"entries={self.collection.count()}, persist={persist_dir}"
            )
        except Exception as e:
            self.enabled = False
            logger.warning(f"SemanticCacheManager init failed, disabling: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def get(
        self,
        provider: str,
        model: str,
        messages: List[dict],
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Look up a semantically similar cached response.

        Returns:
            (response_dict, hit_type) where hit_type is one of:
              "semantic_hit" — a similar (but not identical) prompt was found
              "miss"         — no similar response found
        """
        if not self.enabled or self.collection is None:
            return None, "miss"

        query_text = _extract_text_for_embedding(messages)
        if not query_text:
            return None, "miss"

        namespace = f"{provider}::{model}"

        try:
            count = self.collection.count()
            if count == 0:
                self.stats["misses"] += 1
                return None, "miss"

            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(1, count),
                where={"namespace": namespace},
                include=["metadatas", "distances"],
            )

            if not results["ids"] or not results["ids"][0]:
                self.stats["misses"] += 1
                return None, "miss"

            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity: similarity = 1 - distance
            distance = results["distances"][0][0]
            similarity = 1.0 - distance

            if similarity >= self.threshold:
                metadata = results["metadatas"][0][0]
                cached_response = json.loads(metadata["response_json"])
                self.stats["semantic_hits"] += 1
                logger.info(
                    f"🔮 Semantic Cache HIT (similarity={similarity:.3f} ≥ {self.threshold}): "
                    f"{provider}/{model}"
                )
                return cached_response, "semantic_hit"
            else:
                self.stats["misses"] += 1
                logger.debug(
                    f"🔮 Semantic Cache MISS (similarity={similarity:.3f} < {self.threshold})"
                )
                return None, "miss"

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(f"SemanticCache get error: {e}")
            return None, "miss"

    def set(
        self,
        provider: str,
        model: str,
        messages: List[dict],
        response: Dict[str, Any],
    ) -> bool:
        """Store a response in the semantic cache."""
        if not self.enabled or self.collection is None:
            return False

        query_text = _extract_text_for_embedding(messages)
        if not query_text:
            return False

        doc_id = _make_exact_key(provider, model, messages)
        namespace = f"{provider}::{model}"

        try:
            self.collection.upsert(
                ids=[doc_id],
                documents=[query_text],
                metadatas=[{
                    "namespace": namespace,
                    "provider": provider,
                    "model": model,
                    "response_json": json.dumps(response),
                }],
            )
            logger.debug(f"🔮 Semantic Cache STORED: {doc_id[:16]}… ({namespace})")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(f"SemanticCache set error: {e}")
            return False

    def clear(self) -> bool:
        """Delete and recreate the entire ChromaDB collection."""
        if not self.enabled or self.collection is None:
            return False
        try:
            self._client.delete_collection(COLLECTION_NAME)
            self.collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self._ef,
                metadata={"hnsw:space": "cosine"},
            )
            self.stats = {"semantic_hits": 0, "misses": 0, "errors": 0}
            logger.info("🔮 Semantic Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"SemanticCache clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["semantic_hits"] + self.stats["misses"]
        hit_rate = (self.stats["semantic_hits"] / total * 100) if total > 0 else 0.0
        return {
            "semantic_hits": self.stats["semantic_hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "total": total,
            "semantic_hit_rate_percent": round(hit_rate, 2),
            "threshold": self.threshold,
            "total_stored": self.collection.count() if self.collection else 0,
            "enabled": self.enabled,
        }

    def count(self) -> int:
        if self.collection is None:
            return 0
        return self.collection.count()


# ──────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────
_semantic_cache: Optional[SemanticCacheManager] = None


def get_semantic_cache(
    enabled: bool = True,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> SemanticCacheManager:
    """Get or create the global SemanticCacheManager singleton."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCacheManager(
            enabled=enabled,
            similarity_threshold=similarity_threshold,
        )
    return _semantic_cache
