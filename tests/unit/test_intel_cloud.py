from __future__ import annotations

from types import SimpleNamespace

import holdspeak.intel as intel_module
from holdspeak.intel import MeetingIntel, resolve_intel_provider, get_cloud_intel_runtime_status


def test_resolve_provider_auto_falls_back_to_cloud(monkeypatch) -> None:
    monkeypatch.setattr(intel_module, "Llama", None)
    monkeypatch.setattr(intel_module, "OpenAI", object)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    provider, reason = resolve_intel_provider(
        "auto",
        model_path="/missing/local/model.gguf",
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
    )

    assert reason is None
    assert provider == "cloud"


def test_get_cloud_runtime_status_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr(intel_module, "OpenAI", object)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    ok, reason = get_cloud_intel_runtime_status(
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
    )

    assert ok is False
    assert reason is not None
    assert "OPENAI_API_KEY" in reason


def test_get_cloud_runtime_status_rejects_invalid_base_url(monkeypatch) -> None:
    monkeypatch.setattr(intel_module, "OpenAI", object)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    ok, reason = get_cloud_intel_runtime_status(
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url="api.example.com/v1",
    )

    assert ok is False
    assert reason is not None
    assert "Invalid cloud base URL" in reason


def test_meeting_intel_cloud_uses_base_url_and_parses_response(monkeypatch) -> None:
    calls: list[dict] = []

    class _FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"topics":["Roadmap"],"action_items":[{"task":"Ship cloud mode","owner":"Me","due":null}],"summary":"Planned cloud launch."}'
                        )
                    )
                ]
            )

    class _FakeOpenAI:
        instances: list[dict] = []

        def __init__(self, **kwargs):
            self.__class__.instances.append(kwargs)
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    intel = MeetingIntel(
        provider="cloud",
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url="https://api.example.com/v1",
    )

    result = intel.analyze("[00:00:00] Me: let's ship this", stream=False)

    assert _FakeOpenAI.instances
    assert _FakeOpenAI.instances[0]["base_url"] == "https://api.example.com/v1"
    assert calls and calls[0]["model"] == "gpt-5-mini"
    assert result.summary == "Planned cloud launch."
    assert result.topics == ["Roadmap"]
    assert len(result.action_items) == 1
    assert result.action_items[0].task == "Ship cloud mode"


def test_meeting_intel_cloud_falls_back_to_max_completion_tokens(monkeypatch) -> None:
    create_calls: list[dict] = []

    class _FakeCompletions:
        def create(self, **kwargs):
            create_calls.append(kwargs)
            if "max_tokens" in kwargs:
                raise TypeError("unknown argument: max_tokens")
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"topics":[],"action_items":[],"summary":"ok"}'
                        )
                    )
                ]
            )

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            _ = kwargs
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    intel = MeetingIntel(provider="cloud", cloud_model="gpt-5-mini")
    result = intel.analyze("[00:00:00] Me: test", stream=False)

    assert result.summary == "ok"
    assert len(create_calls) == 2
    assert "max_tokens" in create_calls[0]
    assert "max_completion_tokens" in create_calls[1]


def test_meeting_intel_cloud_surfaces_timeout_errors(monkeypatch) -> None:
    class _FakeCompletions:
        def create(self, **kwargs):
            _ = kwargs
            raise TimeoutError("request timed out")

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            _ = kwargs
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    intel = MeetingIntel(provider="cloud", cloud_model="gpt-5-mini")
    result = intel.analyze("[00:00:00] Me: test", stream=False)

    assert result.error is not None
    assert "timed out" in result.error.lower()


def test_meeting_intel_cloud_surfaces_auth_errors(monkeypatch) -> None:
    class _FakeCompletions:
        def create(self, **kwargs):
            _ = kwargs
            raise RuntimeError("401 Unauthorized")

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            _ = kwargs
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    intel = MeetingIntel(provider="cloud", cloud_model="gpt-5-mini")
    result = intel.analyze("[00:00:00] Me: test", stream=False)

    assert result.error is not None
    assert "auth failed" in result.error.lower()


def test_meeting_intel_cloud_surfaces_model_not_found_errors(monkeypatch) -> None:
    class _FakeCompletions:
        def create(self, **kwargs):
            _ = kwargs
            raise RuntimeError("404 model not found")

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            _ = kwargs
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    intel = MeetingIntel(provider="cloud", cloud_model="qwen2.5-32b-instruct")
    result = intel.analyze("[00:00:00] Me: test", stream=False)

    assert result.error is not None
    assert "model 'qwen2.5-32b-instruct' not found" in result.error.lower()
