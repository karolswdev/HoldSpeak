from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.intel as intel_module
from holdspeak.intel import MeetingIntel, resolve_intel_provider, get_cloud_intel_runtime_status

from holdspeak.intel.providers import configured_meeting_intel
from tests.unit.admitted_context import admitted_context



def _configured_intel():
    """The ONE configured-construction entrance (HS-131-14).

    The old public uncontextual factory is gone: the body is private and reachable
    only through ``configured_meeting_intel``, which refuses without the dispatch
    context an admitted child carries. The placement assertions below are unchanged
    — what changed is that reaching the constructor now requires admission.
    """
    revision = SimpleNamespace(id="dep_configured", destination_id="configured")
    return configured_meeting_intel(
        context=admitted_context(revision=revision), revision=revision
    )

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


def test_configured_meeting_intel_reads_the_assigned_target(monkeypatch) -> None:
    # Plugins must honour the user's assigned InferenceTarget, not
    # MeetingIntel() bare module defaults (HS-27-02, retargeted HS-112-01:
    # the endpoint lives ONLY in the profiles table).
    from holdspeak.db.models import ProfileRecord

    cfg = SimpleNamespace(
        meeting=SimpleNamespace(
            intel_provider="cloud",
            intel_cloud_reasoning_effort=None,
            intel_cloud_store=False,
            intel_realtime_model=None,
            intel_profile_id="p-43",
        )
    )
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: ProfileRecord(
            id=pid,
            name="LAN llama",
            kind="openAICompatible",
            base_url="http://192.168.1.43:8080/v1",
            model="Qwen3.5-9B-UD-Q6_K_XL.gguf",
        ),
    )

    intel = _configured_intel()
    assert intel.provider == "cloud"
    assert intel.cloud_base_url == "http://192.168.1.43:8080/v1"
    assert intel.cloud_model == "Qwen3.5-9B-UD-Q6_K_XL.gguf"


def test_get_cloud_runtime_status_allows_self_hosted_base_url_without_key(monkeypatch) -> None:
    # llama.cpp / LM Studio / Ollama ignore the key; a custom base_url should
    # resolve even with no OPENAI_API_KEY set.
    monkeypatch.setattr(intel_module, "OpenAI", object)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    ok, reason = get_cloud_intel_runtime_status(
        cloud_model="Qwen3.5-9B-UD-Q6_K_XL.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url="http://192.168.1.43:8080/v1",
    )

    assert ok is True
    assert reason is None


def test_meeting_intel_self_hosted_uses_placeholder_key(monkeypatch) -> None:
    class _FakeCompletions:
        def create(self, **kwargs):
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
        instances: list[dict] = []

        def __init__(self, **kwargs):
            self.__class__.instances.append(kwargs)
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    intel = MeetingIntel(
        provider="cloud",
        cloud_model="Qwen3.5-9B-UD-Q6_K_XL.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url="http://192.168.1.43:8080/v1",
    )
    result = intel.analyze("[00:00:00] Me: ship it", stream=False)

    assert result.summary == "ok"
    assert _FakeOpenAI.instances
    assert _FakeOpenAI.instances[0]["api_key"] == intel_module.SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER
    assert _FakeOpenAI.instances[0]["base_url"] == "http://192.168.1.43:8080/v1"


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
    from holdspeak.intel.engine import forget_endpoint_dialects
    from holdspeak.kernel.provider_signals import ProviderCompatibilityRetry

    forget_endpoint_dialects()
    try:
        intel = MeetingIntel(provider="cloud", cloud_model="gpt-5-mini")

        # HS-131-10 (Sol Amendment 3): the fallback used to send a SECOND
        # `create` inside this one call — two requests to a model under one
        # admitted child and one receipt. The engine now makes exactly ONE
        # physical request and NAMES the dialect instead of hiding a retry.
        with pytest.raises(ProviderCompatibilityRetry) as signal:
            intel.analyze("[00:00:00] Me: test", stream=False)
        assert signal.value.mode == "max_completion_tokens"
        assert len(create_calls) == 1
        assert "max_tokens" in create_calls[0]

        # The endpoint's dialect is remembered, so the SECOND admitted child
        # (the runner submits it; see test_one_path_cardinality.py) speaks it on
        # its first and only request, and the compatibility behaviour is kept.
        second = MeetingIntel(provider="cloud", cloud_model="gpt-5-mini")
        result = second.analyze("[00:00:00] Me: test", stream=False)

        assert result.summary == "ok"
        assert len(create_calls) == 2
        assert "max_completion_tokens" in create_calls[1]
        assert "max_tokens" not in create_calls[1]
    finally:
        forget_endpoint_dialects()


def test_meeting_intel_429_is_typed_no_generation_not_sanitized_text(monkeypatch) -> None:
    class _RateLimited(RuntimeError):
        status_code = 429

    class _FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda **_kwargs: (_ for _ in ()).throw(_RateLimited("secret body")))
            )

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from holdspeak.kernel.provider_signals import ProviderKnownNoGenerationTransient

    with pytest.raises(ProviderKnownNoGenerationTransient):
        MeetingIntel(provider="cloud", cloud_model="gpt-5-mini").analyze(
            "[00:00:00] Me: test", stream=False
        )


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
