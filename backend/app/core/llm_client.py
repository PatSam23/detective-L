"""LLM client configuration using the internal gateway."""

from __future__ import annotations

import os
from typing import Iterable, List

import httpx
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

load_dotenv()


GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8000")
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))


def _message_role(message: BaseMessage) -> str:
    if isinstance(message, SystemMessage):
        return "system"
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    return getattr(message, "role", None) or getattr(message, "type", "user")


def _normalize_messages(input_value) -> List[dict]:
    if hasattr(input_value, "to_messages"):
        messages: Iterable[BaseMessage] = input_value.to_messages()
    elif isinstance(input_value, BaseMessage):
        messages = [input_value]
    else:
        messages = [HumanMessage(content=str(input_value))]

    payload = []
    for message in messages:
        payload.append({
            "role": _message_role(message),
            "content": message.content if isinstance(message.content, str) else str(message.content),
        })
    return payload


def _gateway_payload(messages: List[dict], provider: str, model: str, temperature: float, max_tokens: int) -> dict:
    return {
        "provider": provider,
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _call_gateway(messages: List[dict], provider: str, model: str, temperature: float, max_tokens: int) -> str:
    payload = _gateway_payload(messages, provider, model, temperature, max_tokens)
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{GATEWAY_BASE_URL}/gateway/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("content", "")


async def _acall_gateway(messages: List[dict], provider: str, model: str, temperature: float, max_tokens: int) -> str:
    payload = _gateway_payload(messages, provider, model, temperature, max_tokens)
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{GATEWAY_BASE_URL}/gateway/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("content", "")


def get_llm(
    temperature: float = 0.7,
    model: str | None = None,
    provider: str | None = None,
    max_tokens: int | None = None,
) -> RunnableLambda:
    model_name = model or DEFAULT_MODEL
    provider_name = provider or DEFAULT_PROVIDER
    max_output_tokens = max_tokens or DEFAULT_MAX_TOKENS

    def _invoke(input_value):
        messages = _normalize_messages(input_value)
        content = _call_gateway(messages, provider_name, model_name, temperature, max_output_tokens)
        return AIMessage(content=content)

    async def _ainvoke(input_value):
        messages = _normalize_messages(input_value)
        content = await _acall_gateway(messages, provider_name, model_name, temperature, max_output_tokens)
        return AIMessage(content=content)

    return RunnableLambda(_invoke, afunc=_ainvoke)


llm = get_llm(temperature=0.5)
llm_creative = get_llm(temperature=0.8)
llm_strict = get_llm(temperature=0.2)
