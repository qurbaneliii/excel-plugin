from app.settings import get_settings


def test_settings_loading(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "false")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "llama3.2:3b")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.llm_provider == "local"
    assert settings.local_llm_enabled is False
    assert settings.local_llm_model == "llama3.2:3b"
    get_settings.cache_clear()
