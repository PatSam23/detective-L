from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import logging
import asyncio
import os
 
from app.core.graph import arun_research, astream_research, research_app
from app.gateway.router import router as gateway_router
from app.gateway.cache import get_cache_manager
from app.core.llm_client import GatewayConfig
from app.schemas import ResearchRequest, ResearchResponse
from app.db.database import init_db, close_db, AsyncSessionLocal
from app.db.models import LLMUsageLog
from sqlalchemy import select, func, desc
from prometheus_fastapi_instrumentator import Instrumentator

# Setup minimal file logger specifically for API entry if needed
logger = logging.getLogger("api")

app = FastAPI(
    title="Detective-L Research API",
    description="Multi-agent parallel research intelligence system",
    version="1.0.0"
)

# Initialize Prometheus Metrics
Instrumentator().instrument(app).expose(app)

app.include_router(gateway_router)

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize Redis cache on app startup."""
    cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    cache_ttl = int(os.getenv("CACHE_TTL", 86400))
    
    cache = get_cache_manager(
        enabled=cache_enabled,
        redis_host=redis_host,
        redis_port=redis_port,
        default_ttl=cache_ttl
    )
    
    if cache_enabled:
        logger.info(f"Redis Cache initialized (enabled={cache_enabled}, TTL={cache_ttl}s)")
    else:
        logger.info("Redis Cache disabled")
    
    # Initialize Database
    await init_db()
    logger.info("PostgreSQL Analytics initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis cache connection on app shutdown."""
    cache = get_cache_manager(enabled=False)
    cache.close()
    logger.info("🔌 Redis cache connection closed")
    
    # Close Database
    await close_db()
    logger.info("🔌 PostgreSQL connection closed")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "detective-l"}


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics (hits, misses, hit rate)."""
    cache = get_cache_manager(enabled=False)  # Don't create new instance
    stats = cache.get_stats()
    return {
        "cache": stats,
        "message": "Cache statistics (track LLM call reduction)"
    }


@app.post("/cache/clear")
async def clear_cache():
    """Clear all Redis cache entries and statistics."""
    cache = get_cache_manager(enabled=False)
    success = cache.clear()
    cache.reset_stats()
    return {
        "success": success,
        "message": "Cache cleared successfully" if success else "Cache clearing failed"
    }


@app.get("/gateway/config")
async def get_gateway_config():
    """Get active gateway configurations."""
    return {
        "provider": GatewayConfig.provider,
        "model": GatewayConfig.model,
        "max_tokens": GatewayConfig.max_tokens,
        "cache_enabled": GatewayConfig.cache_enabled
    }


@app.post("/gateway/config")
async def update_gateway_config(config: dict):
    """Update gateway configurations at runtime."""
    if "provider" in config:
        GatewayConfig.provider = config["provider"]
    if "model" in config:
        GatewayConfig.model = config["model"]
    if "max_tokens" in config:
        GatewayConfig.max_tokens = int(config["max_tokens"])
    if "cache_enabled" in config:
        GatewayConfig.cache_enabled = config["cache_enabled"]
        cache = get_cache_manager(enabled=False)
        cache.enabled = config["cache_enabled"]
        if cache.enabled and not cache.connected:
            cache._connect()
            
    return {
        "success": True,
        "config": {
            "provider": GatewayConfig.provider,
            "model": GatewayConfig.model,
            "max_tokens": GatewayConfig.max_tokens,
            "cache_enabled": GatewayConfig.cache_enabled
        }
    }


@app.get("/analytics/usage")
async def get_usage_analytics():
    """Get aggregate usage statistics from PostgreSQL."""
    try:
        async with AsyncSessionLocal() as session:
            # Total requests
            total_reqs = await session.scalar(select(func.count(LLMUsageLog.id)))
            
            # Cache hit rate
            cache_hits = await session.scalar(select(func.count(LLMUsageLog.id)).where(LLMUsageLog.cache_hit == True))
            hit_rate = (cache_hits / total_reqs * 100) if total_reqs > 0 else 0
            
            # Total tokens
            total_tokens = await session.scalar(select(func.sum(LLMUsageLog.total_tokens))) or 0
            
            # Avg latency
            avg_latency = await session.scalar(select(func.avg(LLMUsageLog.latency_ms))) or 0
            
            # Recent logs (last 10)
            result = await session.execute(
                select(LLMUsageLog)
                .order_by(desc(LLMUsageLog.created_at))
                .limit(10)
            )
            recent_logs = result.scalars().all()
            
            return {
                "summary": {
                    "total_requests": total_reqs,
                    "cache_hits": cache_hits,
                    "cache_hit_rate": f"{hit_rate:.2f}%",
                    "total_tokens": total_tokens,
                    "avg_latency_ms": f"{avg_latency:.2f}"
                },
                "recent_activity": [
                    {
                        "provider": log.provider,
                        "model": log.model,
                        "tokens": log.total_tokens,
                        "latency": f"{log.latency_ms:.2f}ms",
                        "cache_hit": log.cache_hit,
                        "time": log.created_at.isoformat()
                    } for log in recent_logs
                ]
            }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        return {"error": "Failed to fetch analytics"}


@app.post("/research", response_model=ResearchResponse)
async def run_research_sync(request: ResearchRequest):
    """
    Execute the research pipeline synchronously. 
    This blocks until all agents complete and the final report is generated.
    """
    try:
        logger.info(f"Received sync research request: {request.query}")
        # Run graph
        result = await arun_research(request.query, verbose=False)
        
        return ResearchResponse(
            status="success",
            final_report=result.get("final_report", {}),
            sources=result.get("sources", []),
            revision_count=result.get("revision_count", 0)
        )
    except Exception as e:
        logger.error(f"Error in research processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/stream")
async def stream_research_events(request: ResearchRequest):
    """
    Execute research pipeline and stream SSE events for each agent's progress.
    Sends agent_start, agent_update, and agent_complete events for proper frontend tracking.
    """
    logger.info(f"Received streaming research request: {request.query}")
    
    async def generate_events():
        try:
            agent_started = set()  # Track which agents have sent start event
            
            async for event in astream_research(request.query):
                # Process each node in the event
                for node_name, state_update in event.items():
                    # Send agent_start event on first appearance
                    if node_name not in agent_started:
                        agent_started.add(node_name)
                        start_payload = {
                            "type": "agent_start",
                            "name": node_name,
                        }
                        yield f"data: {json.dumps(start_payload)}\n\n"
                        logger.debug(f"Sent agent_start for {node_name}")
                    
                    # Filter out large/non-serializable data to reduce payload size
                    filtered_update = {}
                    for key, value in state_update.items():
                        # Skip large lists/strings to minimize payload
                        if key in ["research_findings", "draft_report"]:
                            if isinstance(value, list):
                                filtered_update[key] = f"<{len(value)} items>"
                            elif isinstance(value, str):
                                filtered_update[key] = f"<{len(value)} chars>"
                        else:
                            try:
                                json.dumps(value)  # Test serializability
                                filtered_update[key] = value
                            except (TypeError, ValueError):
                                filtered_update[key] = str(value)
                    
                    # Send agent_update with filtered data
                    update_payload = {
                        "type": "agent_update",
                        "name": node_name,
                        "data": filtered_update
                    }
                    yield f"data: {json.dumps(update_payload)}\n\n"
                    
                    # Send agent_complete after processing
                    # (in LangGraph streaming, each event means the node has completed)
                    complete_payload = {
                        "type": "agent_complete",
                        "name": node_name,
                    }
                    yield f"data: {json.dumps(complete_payload)}\n\n"
                    logger.debug(f"Sent agent_complete for {node_name}")
                    
            # Send final explicit completion event
            research_complete_payload = {
                "type": "research_complete"
            }
            yield f"data: {json.dumps(research_complete_payload)}\n\n"
            logger.info("Research stream completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_payload = {
                "type": "error",
                "message": str(e)
            }
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
