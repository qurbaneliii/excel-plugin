from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

ProviderMode = Literal["auto", "openai", "local", "fallback"]

load_dotenv()


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4.1-mini")
    llm_provider: ProviderMode = Field(default="auto")
    local_llm_enabled: bool = Field(default=True)
    local_llm_provider: str = Field(default="ollama")
    local_llm_base_url: str = Field(default="http://localhost:11434/v1")
    local_llm_model: str = Field(default="qwen3:4b")
    local_llm_timeout_seconds: int = Field(default=120)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        llm_provider=(os.getenv("LLM_PROVIDER", "auto").strip().lower() or "auto"),
        local_llm_enabled=_parse_bool(os.getenv("LOCAL_LLM_ENABLED"), True),
        local_llm_provider=os.getenv("LOCAL_LLM_PROVIDER", "ollama"),
        local_llm_base_url=os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
        local_llm_model=os.getenv("LOCAL_LLM_MODEL", "qwen3:4b"),
        local_llm_timeout_seconds=int(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "120")),
    )
