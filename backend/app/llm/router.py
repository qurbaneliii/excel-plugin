from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from pydantic import BaseModel

from ..settings import ProviderMode, Settings
from .base import LLMProvider, ProviderError
from .fallback_provider import FallbackProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider


@dataclass
class RouterResult:
    response: BaseModel
    selected_provider: str
    model: str | None
    fallback_used: bool
    warnings: list[str]
    provider_mode: ProviderMode


class LLMRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.openai_provider = OpenAIProvider(settings)
        self.local_provider = OllamaProvider(settings)
        self.fallback_provider = FallbackProvider()

    def get_status(self) -> dict[str, Any]:
        warnings: list[str] = []
        openai_available = self.openai_provider.is_available()
        local_enabled = self.settings.local_llm_enabled
        local_available = self.local_provider.is_available() if local_enabled else False
        if not openai_available:
            warnings.append("OpenAI provider is not configured or unavailable.")
        if local_enabled and not local_available:
            warnings.append("Local Ollama provider is enabled but not reachable.")
        if not local_enabled:
            warnings.append("Local LLM provider is disabled in settings.")
        return {
            "provider_mode": self.settings.llm_provider,
            "openai_available": openai_available,
            "local_enabled": local_enabled,
            "local_available": local_available,
            "local_provider": self.settings.local_llm_provider,
            "local_base_url": self.settings.local_llm_base_url,
            "local_model": self.settings.local_llm_model,
            "fallback_available": True,
            "warnings": warnings,
        }

    def test_local(self, prompt: str) -> dict[str, Any]:
        if not self.local_provider.is_available():
            return {
                "ok": False,
                "provider": self.settings.local_llm_provider,
                "model": self.settings.local_llm_model,
                "response": None,
                "error": "Local Ollama provider is unavailable.",
            }
        try:
            response = self.local_provider.test_prompt(prompt)
            return {
                "ok": True,
                "provider": self.settings.local_llm_provider,
                "model": self.settings.local_llm_model,
                "response": response,
                "error": None,
            }
        except ProviderError as exc:
            return {
                "ok": False,
                "provider": self.settings.local_llm_provider,
                "model": self.settings.local_llm_model,
                "response": None,
                "error": str(exc),
            }

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: Type[BaseModel],
        task_type: str,
        provider_mode_override: ProviderMode | None = None,
    ) -> RouterResult:
        provider_mode = provider_mode_override or self.settings.llm_provider
        warnings: list[str] = []
        providers = self._providers_for_task(provider_mode, task_type)

        for provider in providers:
            if provider.name != "fallback" and not provider.is_available():
                warnings.append(f"{provider.name} provider unavailable for task '{task_type}'.")
                continue
            try:
                response = provider.generate_json(system_prompt, user_payload, response_model, task_type)
                fallback_used = provider.name == "fallback"
                if fallback_used:
                    warnings.append("Deterministic fallback provider was used.")
                return RouterResult(
                    response=response,
                    selected_provider=provider.name,
                    model=provider.model_name,
                    fallback_used=fallback_used,
                    warnings=warnings,
                    provider_mode=provider_mode,
                )
            except ProviderError as exc:
                warnings.append(f"{provider.name} provider failed: {exc}")

        response = self.fallback_provider.generate_json(system_prompt, user_payload, response_model, task_type)
        warnings.append("Deterministic fallback provider was used after provider failures.")
        return RouterResult(
            response=response,
            selected_provider=self.fallback_provider.name,
            model=self.fallback_provider.model_name,
            fallback_used=True,
            warnings=warnings,
            provider_mode=provider_mode,
        )

    def _providers_for_task(self, provider_mode: ProviderMode, task_type: str) -> list[LLMProvider]:
        if provider_mode == "openai":
            return [self.openai_provider, self.fallback_provider]
        if provider_mode == "local":
            return [self.local_provider, self.fallback_provider]
        if provider_mode == "fallback":
            return [self.fallback_provider]

        if task_type == "formula_explain":
            return [self.local_provider, self.openai_provider, self.fallback_provider]
        if task_type in {"formula_generate", "formula_fix", "action_plan"}:
            return [self.openai_provider, self.local_provider, self.fallback_provider]
        if task_type in {"range_analysis", "report"}:
            return [self.local_provider, self.openai_provider, self.fallback_provider]
        if task_type == "summary_sheet":
            return [self.fallback_provider]
        return [self.openai_provider, self.local_provider, self.fallback_provider]
