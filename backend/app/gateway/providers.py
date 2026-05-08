"""Provider implementations for the LLM gateway."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

import httpx

from app.gateway.schemas import GatewayChatRequest, GatewayChatResponse


OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _split_system(messages: List[dict]) -> Tuple[Optional[str], List[dict]]:
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    remaining = [m for m in messages if m["role"] != "system"]
    system_text = "\n\n".join(system_parts).strip() if system_parts else None
    return system_text, remaining


async def _call_openai(request: GatewayChatRequest) -> GatewayChatResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    payload = {
        "model": request.model,
        "messages": [m.model_dump() for m in request.messages],
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(OPENAI_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage")

    return GatewayChatResponse(
        provider=request.provider,
        model=request.model,
        content=content,
        usage=usage,
    )


async def _call_anthropic(request: GatewayChatRequest) -> GatewayChatResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    system_text, remaining = _split_system([m.model_dump() for m in request.messages])
    payload = {
        "model": request.model,
        "messages": remaining,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    if system_text:
        payload["system"] = system_text

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(ANTHROPIC_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content_parts = data.get("content", [])
    content = "".join(part.get("text", "") for part in content_parts)
    usage = data.get("usage")

    return GatewayChatResponse(
        provider=request.provider,
        model=request.model,
        content=content,
        usage=usage,
    )


def _gemini_contents(messages: List[dict]) -> List[dict]:
    system_text, remaining = _split_system(messages)
    contents = []

    for msg in remaining:
        role = "user" if msg["role"] == "user" else "model"
        text = msg["content"]
        contents.append({"role": role, "parts": [{"text": text}]})

    if system_text:
        if contents and contents[0]["role"] == "user":
            contents[0]["parts"][0]["text"] = f"{system_text}\n\n{contents[0]['parts'][0]['text']}"
        else:
            contents.insert(0, {"role": "user", "parts": [{"text": system_text}]})

    return contents


async def _call_gemini(request: GatewayChatRequest) -> GatewayChatResponse:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")

    contents = _gemini_contents([m.model_dump() for m in request.messages])
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        },
    }

    url = GEMINI_URL_TEMPLATE.format(model=request.model)
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, params={"key": api_key}, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        content = ""
    else:
        parts = candidates[0].get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in parts)

    return GatewayChatResponse(
        provider=request.provider,
        model=request.model,
        content=content,
        usage=None,
    )


async def call_provider(request: GatewayChatRequest) -> GatewayChatResponse:
    provider = request.provider.lower()
    if provider == "openai":
        return await _call_openai(request)
    if provider == "anthropic":
        return await _call_anthropic(request)
    if provider == "gemini":
        return await _call_gemini(request)

    raise ValueError(f"Unsupported provider: {request.provider}")
