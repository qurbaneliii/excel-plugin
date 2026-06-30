from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel


class ProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    name: str
    model_name: str | None

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: Type[BaseModel],
        task_type: str,
    ) -> BaseModel:
        raise NotImplementedError

    @abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str, task_type: str) -> str:
        raise NotImplementedError
