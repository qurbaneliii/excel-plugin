from __future__ import annotations

from typing import Any, Type

from openai import OpenAI
from pydantic import BaseModel

from ..prompts import JSON_REPAIR_PROMPT
from ..settings import Settings
from .base import LLMProvider, ProviderError
from .json_utils import dump_payload, normalize_json_text, validate_response_model


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        self.model_name = settings.openai_model
        self._client = OpenAI(api_key=settings.openai_api_key, timeout=settings.local_llm_timeout_seconds) if settings.openai_api_key else None

    def is_available(self) -> bool:
        return self._client is not None

    def generate_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: Type[BaseModel],
        task_type: str,
    ) -> BaseModel:
        if not self._client:
            raise ProviderError("OpenAI provider is not configured.")

        content = self._chat_json(
            system_prompt=(
                f"{system_prompt}\n"
                f"Return one JSON object only and make it match this schema exactly: {response_model.model_json_schema()}"
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
            raise ProviderError("OpenAI provider is not configured.")
        return self._chat_text(system_prompt, user_prompt)

    def _repair_json(self, invalid_content: str, response_model: Type[BaseModel]) -> str:
        if not self._client:
            raise ProviderError("OpenAI provider is not configured.")
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
            raise ProviderError("OpenAI provider is not configured.")
        response = self._client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ProviderError("OpenAI returned no content.")
        return content

    def _chat_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            raise ProviderError("OpenAI provider is not configured.")
        response = self._client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ProviderError("OpenAI returned no content.")
        return content
