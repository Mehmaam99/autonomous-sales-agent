from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.llm_gateway import LLMGateway


def test_gateway_uses_configured_groq_model(monkeypatch):
    monkeypatch.setattr(
        "app.core.llm_gateway.settings.groq_api_key",
        "test-api-key",
    )

    fake_config = SimpleNamespace(
        llm=SimpleNamespace(
            provider="groq",
            models={"default": "llama-3.3-70b-versatile"},
            generation=SimpleNamespace(temperature=0.2, max_tokens=2000),
        )
    )

    monkeypatch.setattr(
        "app.core.llm_gateway.load_application_config",
        lambda niche: fake_config,
    )

    mock_client = MagicMock()
    monkeypatch.setattr(
        "app.core.llm_gateway.Groq",
        lambda api_key: mock_client,
    )

    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="  Hello from Groq  ")
            )
        ]
    )

    gateway = LLMGateway("real_estate")
    result = gateway.generate(
        "Say hello",
        system_prompt="You are a helpful assistant.",
    )

    assert result == "Hello from Groq"
    mock_client.chat.completions.create.assert_called_once_with(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"},
        ],
        temperature=0.2,
        max_tokens=2000,
    )


def test_gateway_rejects_missing_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.core.llm_gateway.settings.groq_api_key",
        None,
    )

    with pytest.raises(RuntimeError, match="GROQ_API_KEY is missing"):
        LLMGateway("real_estate")


def test_gateway_rejects_empty_prompt(monkeypatch):
    monkeypatch.setattr(
        "app.core.llm_gateway.settings.groq_api_key",
        "test-api-key",
    )

    fake_config = SimpleNamespace(
        llm=SimpleNamespace(
            provider="groq",
            models={"default": "llama-3.3-70b-versatile"},
            generation=SimpleNamespace(temperature=0.2, max_tokens=2000),
        )
    )

    monkeypatch.setattr(
        "app.core.llm_gateway.load_application_config",
        lambda niche: fake_config,
    )
    monkeypatch.setattr(
        "app.core.llm_gateway.Groq",
        lambda api_key: MagicMock(),
    )

    gateway = LLMGateway("real_estate")

    with pytest.raises(ValueError, match="Prompt must not be empty"):
        gateway.generate("   ")
