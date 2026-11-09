"""FastAPI router for the LLM gateway endpoint."""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.gateway.schemas import GatewayChatRequest, GatewayChatResponse
from app.gateway.providers import call_provider
from app.gateway.cache import get_cache_manager
from app.gateway.semantic_cache import get_semantic_cache
from app.gateway.rate_limiter import verify_rate_limit
from app.db.database import AsyncSessionLocal
from app.db.models import LLMUsageLog
import time

logger = logging.getLogger("gateway")

router = APIRouter(tags=["gateway"])


async def log_usage_to_db(log_data: dict):
    try:
        async with AsyncSessionLocal() as session:
            db_log = LLMUsageLog(**log_data)
            session.add(db_log)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to log LLM usage to DB: {e}")


@router.post("/gateway/chat", response_model=GatewayChatResponse)
async def gateway_chat(
    request: GatewayChatRequest,
    background_tasks: BackgroundTasks,
    _ = Depends(verify_rate_limit),
):
    """
    Gateway chat endpoint with two-tier caching.

    Flow:
    1. Exact hash match  → Redis cache  (instant, identical prompts)
    2. Semantic match    → ChromaDB     (cosine similarity ≥ threshold, paraphrases)
    3. Miss              → call LLM provider, store in both caches
    """
    redis_cache = get_cache_manager()
    semantic_cache = get_semantic_cache()

    try:
        start_time = time.time()
        messages_list = [msg.model_dump() for msg in request.messages]

        # ── Tier 1: Exact Redis cache ──────────────────────────────────
        cached_response = redis_cache.get(request.provider, request.model, messages_list)
        if cached_response:
            latency_ms = (time.time() - start_time) * 1000
            usage = cached_response.get("usage") or {}
            background_tasks.add_task(log_usage_to_db, {
                "provider": request.provider,
                "model": request.model,
                "messages": messages_list,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "response_content": cached_response.get("content", ""),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency_ms": latency_ms,
                "cache_hit": True,
            })
            logger.info(
                f"📦 Exact Cache HIT: {request.provider}/{request.model} "
                f"(stats: {redis_cache.get_stats()})"
            )
            return GatewayChatResponse(**cached_response)

        # ── Tier 2: Semantic vector cache ──────────────────────────────
        semantic_response, hit_type = semantic_cache.get(
            request.provider, request.model, messages_list
        )
        if semantic_response:
            latency_ms = (time.time() - start_time) * 1000
            usage = semantic_response.get("usage") or {}
            background_tasks.add_task(log_usage_to_db, {
                "provider": request.provider,
                "model": request.model,
                "messages": messages_list,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "response_content": semantic_response.get("content", ""),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "latency_ms": latency_ms,
                "cache_hit": True,
            })
            logger.info(
                f"🔮 Semantic Cache HIT: {request.provider}/{request.model} "
                f"(semantic_stats: {semantic_cache.get_stats()})"
            )
            return GatewayChatResponse(**semantic_response)

        # ── Tier 3: Miss → call provider, store in both caches ─────────
        response = await call_provider(request)
        latency_ms = (time.time() - start_time) * 1000

        # Store in Redis (exact) and ChromaDB (semantic)
        redis_cache.set(request.provider, request.model, messages_list, response.model_dump())
        semantic_cache.set(request.provider, request.model, messages_list, response.model_dump())

        usage = response.usage or {}
        background_tasks.add_task(log_usage_to_db, {
            "provider": request.provider,
            "model": request.model,
            "messages": messages_list,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_content": response.content,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cache_hit": False,
        })

        logger.info(
            f"💾 Cache MISS → Stored in Redis + ChromaDB: {request.provider}/{request.model} "
            f"(redis_stats: {redis_cache.get_stats()}, "
            f"semantic_stats: {semantic_cache.get_stats()})"
        )

        return response

    except ValueError as exc:
        logger.error("Gateway error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Gateway failure: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Gateway provider failure")

