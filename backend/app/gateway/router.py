"""FastAPI router for the LLM gateway endpoint."""

import logging
from fastapi import APIRouter, HTTPException

from app.gateway.schemas import GatewayChatRequest, GatewayChatResponse
from app.gateway.providers import call_provider

logger = logging.getLogger("gateway")

router = APIRouter(tags=["gateway"])


@router.post("/gateway/chat", response_model=GatewayChatResponse)
async def gateway_chat(request: GatewayChatRequest):
    try:
        return await call_provider(request)
    except ValueError as exc:
        logger.error("Gateway error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Gateway failure: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Gateway provider failure")
