from pydantic import BaseModel

from app.llm.base import ProviderError
from app.llm.router import LLMRouter
from app.settings import Settings


class DummyResponse(BaseModel):
    value: str


class StubProvider:
    def __init__(self, name: str, available: bool, result: str | None = None, error: str | None = None) -> None:
        self.name = name
        self.model_name = f"{name}-model"
        self.available = available
        self.result = result
        self.error = error

    def is_available(self) -> bool:
        return self.available

    def generate_json(self, system_prompt, user_payload, response_model, task_type):
        if self.error:
            raise ProviderError(self.error)
        return response_model(value=self.result or self.name)

    def generate_text(self, system_prompt, user_prompt, task_type):
        return self.result or self.name


def test_router_auto_prefers_local_for_formula_explain() -> None:
    router = LLMRouter(Settings())
    router.local_provider = StubProvider("local", True, result="local-win")
    router.openai_provider = StubProvider("openai", True, result="openai-win")
    router.fallback_provider = StubProvider("fallback", True, result="fallback-win")

    result = router.generate_json(
        system_prompt="test",
        user_payload={},
        response_model=DummyResponse,
        task_type="formula_explain",
        provider_mode_override="auto",
    )

    assert result.selected_provider == "local"
    assert result.response.value == "local-win"


def test_router_forced_openai_falls_back_when_unavailable() -> None:
    router = LLMRouter(Settings())
    router.openai_provider = StubProvider("openai", False)
    router.local_provider = StubProvider("local", True, result="local-win")
    router.fallback_provider = StubProvider("fallback", True, result="fallback-win")

    result = router.generate_json(
        system_prompt="test",
        user_payload={},
        response_model=DummyResponse,
        task_type="formula_generate",
        provider_mode_override="openai",
    )

    assert result.selected_provider == "fallback"
    assert result.fallback_used is True
    assert any("unavailable" in warning for warning in result.warnings)
