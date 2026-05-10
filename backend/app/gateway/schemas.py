"""Pydantic models for gateway requests and responses."""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class GatewayMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class GatewayChatRequest(BaseModel):
    provider: str = Field(default="gemini", min_length=1)
    model: str = Field(default="gemini-2.5-flash", min_length=1)
    messages: List[GatewayMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class GatewayChatResponse(BaseModel):
    provider: str
    model: str
    content: str
    usage: Optional[Dict[str, int]] = None
