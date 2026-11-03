"""
Gemini Judge implementation for DeepEval.
Inherits from DeepEvalBaseLLM to evaluate metrics using Google Gemini without extra SDKs.
"""

import os
import json
import logging
from typing import Optional, Union, Tuple, Dict, Any
import httpx
from pydantic import BaseModel
from deepeval.models import DeepEvalBaseLLM

logger = logging.getLogger("eval")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiJudge(DeepEvalBaseLLM):
    """DeepEval judge LLM using Google Gemini 2.5 Flash."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self.model_name = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        self.temperature = temperature
        super().__init__(model=model)

    def load_model(self) -> "GeminiJudge":
        return self

    def get_model_name(self) -> str:
        return self.model_name

    def _prepare_payload(self, prompt: str, schema: Optional[BaseModel] = None) -> Dict[str, Any]:
        generation_config = {
            "temperature": self.temperature,
            "maxOutputTokens": 4096,
        }
        if schema is not None:
            generation_config["responseMimeType"] = "application/json"

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": generation_config,
        }

    def generate(
        self,
        prompt: str,
        schema: Optional[BaseModel] = None,
        *args,
        **kwargs,
    ) -> Union[str, BaseModel]:
        """Synchronously generate evaluation verdict or structured output."""
        url = GEMINI_API_URL.format(model=self.model_name)
        payload = self._prepare_payload(prompt, schema)

        with httpx.Client(timeout=60) as client:
            resp = client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "" if schema is None else schema.model_validate({})

        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        if schema is not None:
            try:
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                return schema.model_validate_json(clean_text)
            except Exception as e:
                logger.warning(f"Error parsing Gemini schema response: {e}. Raw text: {text[:200]}")
                return text

        return text

    async def a_generate(
        self,
        prompt: str,
        schema: Optional[BaseModel] = None,
        *args,
        **kwargs,
    ) -> Union[str, BaseModel]:
        """Asynchronously generate evaluation verdict or structured output."""
        url = GEMINI_API_URL.format(model=self.model_name)
        payload = self._prepare_payload(prompt, schema)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, params={"key": self.api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "" if schema is None else schema.model_validate({})

        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        if schema is not None:
            try:
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                return schema.model_validate_json(clean_text)
            except Exception as e:
                logger.warning(f"Error parsing Gemini schema response: {e}. Raw text: {text[:200]}")
                return text

        return text
