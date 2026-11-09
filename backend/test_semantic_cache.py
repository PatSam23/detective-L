"""
Standalone test for SemanticCacheManager (ChromaDB).
Run from project root:
    source venv/bin/activate
    cd backend
    python test_semantic_cache.py
"""

import sys, os, asyncio

# Make sure the backend package is on the path
sys.path.insert(0, os.path.dirname(__file__))

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.gateway.semantic_cache import get_semantic_cache


async def main():
    print("=" * 60)
    print("🔮 Semantic Cache Integration Test")
    print("=" * 60)

    sc = get_semantic_cache()
    if not sc.enabled:
        print("❌ Semantic cache is DISABLED (check SEMANTIC_CACHE_ENABLED in .env)")
        return

    print(f"✅ Semantic cache enabled  |  threshold={sc.threshold}")
    print()

    namespace = "gemini::gemini-2.0-flash"
    q1 = "What are the advantages of Apple Silicon chips?"
    q2 = "Tell me about the benefits of Apple M-series processors"

    # ── 1. Clear any stale data ──────────────────────────────────────
    sc.clear()
    print("🧹 Cache cleared")

    # ── 2. Store a fake response for q1 ─────────────────────────────
    fake_response = {
        "content": "Apple Silicon (M-series) chips deliver industry-leading performance-per-watt, "
                   "unified memory architecture, and tight hardware–software integration resulting in "
                   "exceptional battery life and thermal performance.",
        "tokens": 42,
        "latency_ms": 1200,
    }
    sc.set(q1, fake_response, namespace=namespace)
    print(f"💾 Stored response for:\n   '{q1}'")
    print()

    # ── 3. Exact cache hit ───────────────────────────────────────────
    hit = sc.get(q1, namespace=namespace)
    if hit:
        print(f"✅ EXACT HIT for same query")
    else:
        print(f"❌ MISS on exact query (unexpected!)")
    print()

    # ── 4. Semantic hit with paraphrase ─────────────────────────────
    print(f"🔍 Querying with paraphrase:\n   '{q2}'")
    result = sc.get(q2, namespace=namespace)
    if result:
        print(f"✅ SEMANTIC HIT — similarity above threshold ({sc.threshold})")
        print(f"   Preview: {str(result)[:120]}…")
    else:
        print(f"⚠  MISS — similarity below threshold ({sc.threshold}). Try lowering SEMANTIC_CACHE_THRESHOLD.")
    print()

    # ── 5. Stats ─────────────────────────────────────────────────────
    stats = sc.get_stats()
    print("📊 Cache Stats:")
    for k, v in stats.items():
        print(f"   {k}: {v}")
    print()
    print("=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
