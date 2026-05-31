"""Privacy invariant: no transcript leaves the machine without explicit consent.

These tests lock the egress boundary for meeting intelligence (HS-25-01). The
guarantee is structural, not incidental: with the default ``provider="local"``,
HoldSpeak must never construct or call a cloud (OpenAI) client — even when a
valid cloud API key is sitting right there. Cloud is reached only when the user
explicitly opts in via ``provider="cloud"`` or ``provider="auto"`` (documented
as "local-first, then cloud fallback").

If a future refactor makes ``local`` able to reach the cloud, these tests must
fail. They are the regression guard for the "local-first & private" promise.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.intel as intel_module
from holdspeak.intel import MeetingIntel, intel_egress_posture, resolve_intel_provider
from holdspeak import intel_queue as intel_queue_module


class _CloudClientTracker:
    """Stand-in for ``OpenAI`` that records every construction attempt.

    Any instantiation means a code path tried to reach the cloud. The local
    invariant tests assert this tracker is never constructed.
    """

    instances: list["_CloudClientTracker"] = []

    def __init__(self, **kwargs) -> None:
        type(self).instances.append(self)
        self.kwargs = kwargs
        # Minimal surface so an explicit-cloud path can proceed far enough to
        # prove it *did* construct a client.
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):  # pragma: no cover - not exercised by invariant tests
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))]
        )


@pytest.fixture(autouse=True)
def _reset_tracker(monkeypatch):
    _CloudClientTracker.instances = []
    # A valid-looking key is deliberately present for every test: the local
    # invariant must hold *despite* cloud being readily available.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-present")
    yield
    _CloudClientTracker.instances = []


def test_local_provider_resolves_local_only_never_cloud(monkeypatch):
    """resolve_intel_provider('local') never returns 'cloud', even with a key."""
    monkeypatch.setattr(intel_module, "OpenAI", _CloudClientTracker)
    monkeypatch.setattr(intel_module, "Llama", None)

    provider, reason = resolve_intel_provider(
        "local",
        model_path="/does/not/exist/model.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
    )

    assert provider is None
    assert reason is not None
    assert _CloudClientTracker.instances == []


def test_local_provider_missing_model_never_constructs_cloud_client(monkeypatch):
    """MeetingIntel(provider='local') with no local model fails closed, no egress."""
    monkeypatch.setattr(intel_module, "OpenAI", _CloudClientTracker)
    monkeypatch.setattr(intel_module, "Llama", None)

    intel = MeetingIntel(
        provider="local",
        model_path="/does/not/exist/model.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
    )

    # analyze(stream=False) fails closed: it returns an errored result rather
    # than raising, and crucially never escalates to the cloud.
    result = intel.analyze("Speaker: we discussed the launch plan.", stream=False)

    assert result.error is not None
    assert intel.active_provider != "cloud"
    assert _CloudClientTracker.instances == [], (
        "provider='local' must never construct a cloud client"
    )


def test_deferred_queue_local_provider_never_reaches_cloud(monkeypatch):
    """The deferred-intel worker with provider='local' never touches the cloud."""
    monkeypatch.setattr(intel_module, "OpenAI", _CloudClientTracker)
    monkeypatch.setattr(intel_module, "Llama", None)

    # No local model available + provider='local' → the queue pauses rather than
    # escalating. It must not construct a cloud client to "make progress".
    processed = intel_queue_module.process_next_intel_job(
        model_path="/does/not/exist/model.gguf",
        provider="local",
        cloud_api_key_env="OPENAI_API_KEY",
    )

    assert processed is False
    assert _CloudClientTracker.instances == []


def test_auto_provider_reaches_cloud_when_local_unavailable(monkeypatch):
    """Consent boundary: 'auto' DOES fall back to cloud — we did not cut it out."""
    monkeypatch.setattr(intel_module, "OpenAI", _CloudClientTracker)
    monkeypatch.setattr(intel_module, "Llama", None)

    provider, reason = resolve_intel_provider(
        "auto",
        model_path="/does/not/exist/model.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
    )
    assert reason is None
    assert provider == "cloud"

    # And the explicit path actually constructs the client when loaded.
    intel = MeetingIntel(
        provider="auto",
        model_path="/does/not/exist/model.gguf",
        cloud_api_key_env="OPENAI_API_KEY",
    )
    intel._ensure_runtime_loaded()
    assert intel.active_provider == "cloud"
    assert len(_CloudClientTracker.instances) == 1


def test_explicit_cloud_provider_constructs_cloud_client(monkeypatch):
    """Consent boundary: explicit 'cloud' constructs a cloud client by design."""
    monkeypatch.setattr(intel_module, "OpenAI", _CloudClientTracker)

    intel = MeetingIntel(provider="cloud", cloud_api_key_env="OPENAI_API_KEY")
    intel._ensure_runtime_loaded()

    assert intel.active_provider == "cloud"
    assert len(_CloudClientTracker.instances) == 1


def test_egress_posture_local_cannot_transmit():
    can_transmit, description = intel_egress_posture("local")
    assert can_transmit is False
    assert "never leave" in description.lower()


def test_egress_posture_cloud_and_auto_can_transmit():
    cloud_can, cloud_desc = intel_egress_posture("cloud")
    auto_can, auto_desc = intel_egress_posture("auto")
    assert cloud_can is True
    assert auto_can is True
    # 'auto' must make the cloud-fallback explicit, not silent.
    assert "fall" in auto_desc.lower() or "cloud" in auto_desc.lower()


def test_egress_posture_unknown_provider_defaults_local_safe():
    # Garbage provider normalizes to the safe default ('local'), never to cloud.
    can_transmit, _ = intel_egress_posture("nonsense")
    assert can_transmit is False
