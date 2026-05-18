"""FastAPI router for the LLM gateway endpoint."""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.gateway.schemas import GatewayChatRequest, GatewayChatResponse
from app.gateway.providers import call_provider
from app.gateway.cache import get_cache_manager
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
async def gateway_chat(request: GatewayChatRequest, background_tasks: BackgroundTasks):
    """
    Gateway chat endpoint with Redis caching.

    Flow:
    1. Check Redis cache (key: provider + model + messages hash)
    2. If cache hit: return cached response
    3. If cache miss: call LLM provider
    4. Store response in cache (TTL: 24 hours)
    5. Return response
    """
    cache = get_cache_manager()
    
    try:
        start_time = time.time()
        # Convert messages to dict for caching
        messages_list = [msg.model_dump() for msg in request.messages]

        # Check cache
        cached_response = cache.get(request.provider, request.model, messages_list)
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
                "cache_hit": True
            })

            logger.info(
                f"📦 Cache HIT: {request.provider}/{request.model} "
                f"(stats: {cache.get_stats()})"
            )
            return GatewayChatResponse(**cached_response)

        # Cache miss: call provider
        response = await call_provider(request)
        latency_ms = (time.time() - start_time) * 1000

        # Store in cache
        cache.set(request.provider, request.model, messages_list, response.model_dump())
        
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
            "cache_hit": False
        })

        logger.info(
            f"💾 Cache MISS → Stored: {request.provider}/{request.model} "
            f"(stats: {cache.get_stats()})"
        )

        return response

    except ValueError as exc:
        logger.error("Gateway error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Gateway failure: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Gateway provider failure")
