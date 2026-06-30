from fastapi.testclient import TestClient

from app.main import app


def test_health_and_llm_status_endpoints(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(
        "app.main.router.get_status",
        lambda: {
            "provider_mode": "auto",
            "openai_available": False,
            "local_enabled": True,
            "local_available": False,
            "local_provider": "ollama",
            "local_base_url": "http://localhost:11434/v1",
            "local_model": "qwen3:4b",
            "fallback_available": True,
            "warnings": ["Local Ollama provider is enabled but not reachable."],
        },
    )

    health = client.get("/health")
    status = client.get("/api/llm/status")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert status.status_code == 200
    assert status.json()["provider_mode"] == "auto"
