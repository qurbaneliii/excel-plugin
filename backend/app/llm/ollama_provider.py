from __future__ import annotations

from typing import Any, Type

import httpx
from openai import OpenAI
from pydantic import BaseModel

from ..prompts import JSON_REPAIR_PROMPT
from ..settings import Settings
from .base import LLMProvider, ProviderError
from .json_utils import dump_payload, normalize_json_text, validate_response_model


class OllamaProvider(LLMProvider):
    name = "local"

    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.local_llm_model
        self.base_url = settings.local_llm_base_url.rstrip("/")
        self.timeout_seconds = settings.local_llm_timeout_seconds
        self.enabled = settings.local_llm_enabled and settings.local_llm_provider.lower() == "ollama"
        self._client = (
            OpenAI(
                base_url=self.base_url,
                api_key="ollama",
                timeout=self.timeout_seconds,
            )
            if self.enabled
            else None
        )

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            response = httpx.get(f"{self.base_url}/models", timeout=min(self.timeout_seconds, 10))
            return response.is_success
        except httpx.HTTPError:
            return False

    def generate_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: Type[BaseModel],
        task_type: str,
    ) -> BaseModel:
        if not self._client:
            raise ProviderError("Local Ollama provider is disabled.")

        content = self._chat_json(
            system_prompt=(
                f"{system_prompt}\n"
                f"Return one JSON object only. Do not include markdown, prose, or code fences.\n"
                f"Schema: {response_model.model_json_schema()}"
            ),
            user_content=dump_payload(user_payload),
        )
        try:
            return validate_response_model(normalize_json_text(content), response_model)
        except ProviderError:
            repaired = self._repair_json(content, response_model)
            return validate_response_model(repaired, response_model)

    def generate_text(self, system_prompt: str, user_prompt: str, task_type: str) -> str:
        if not self._client:
            raise ProviderError("Local Ollama provider is disabled.")
        return self._chat_text(system_prompt, user_prompt)

    def test_prompt(self, prompt: str) -> str:
        if not self._client:
            raise ProviderError("Local Ollama provider is disabled.")
        return self._chat_text("Respond briefly.", prompt)

    def _repair_json(self, invalid_content: str, response_model: Type[BaseModel]) -> str:
        repaired = self._chat_json(
            system_prompt=JSON_REPAIR_PROMPT,
            user_content=dump_payload(
                {
                    "schema": response_model.model_json_schema(),
                    "invalid_json": invalid_content,
                }
            ),
        )
        return normalize_json_text(repaired)

    def _chat_json(self, system_prompt: str, user_content: str) -> str:
        if not self._client:
            raise ProviderError("Local Ollama provider is disabled.")
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:  # pragma: no cover - SDK/network dependent
            raise ProviderError(f"Ollama request failed: {exc.__class__.__name__}") from exc
        content = response.choices[0].message.content
        if not content:
            raise ProviderError("Local model returned no content.")
        return content

    def _chat_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            raise ProviderError("Local Ollama provider is disabled.")
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - SDK/network dependent
            raise ProviderError(f"Ollama request failed: {exc.__class__.__name__}") from exc
        content = response.choices[0].message.content
        if not content:
            raise ProviderError("Local model returned no content.")
        return content
