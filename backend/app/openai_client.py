from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from .llm.openai_provider import OpenAIProvider
from .settings import get_settings


class OpenAIJSONClient:
    """Compatibility wrapper retained from the MVP.

    New code should use app.llm.router.LLMRouter instead.
    """

    def __init__(self) -> None:
        self._provider = OpenAIProvider(get_settings())

    @property
    def enabled(self) -> bool:
        return self._provider.is_available()

    def generate_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        schema: Type[BaseModel],
        task_type: str = "legacy",
    ) -> BaseModel:
        return self._provider.generate_json(system_prompt, user_payload, schema, task_type)
