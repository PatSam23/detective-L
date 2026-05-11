"""FastAPI router for the LLM gateway endpoint."""

import logging
from fastapi import APIRouter, HTTPException

from app.gateway.schemas import GatewayChatRequest, GatewayChatResponse
from app.gateway.providers import call_provider
from app.gateway.cache import get_cache_manager

logger = logging.getLogger("gateway")

router = APIRouter(tags=["gateway"])


@router.post("/gateway/chat", response_model=GatewayChatResponse)
async def gateway_chat(request: GatewayChatRequest):
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
        # Convert messages to dict for caching
        messages_list = [msg.model_dump() for msg in request.messages]

        # Check cache
        cached_response = cache.get(request.provider, request.model, messages_list)
        if cached_response:
            logger.info(
                f"📦 Cache HIT: {request.provider}/{request.model} "
                f"(stats: {cache.get_stats()})"
            )
            return GatewayChatResponse(**cached_response)

        # Cache miss: call provider
        response = await call_provider(request)

        # Store in cache
        cache.set(request.provider, request.model, messages_list, response.model_dump())
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
