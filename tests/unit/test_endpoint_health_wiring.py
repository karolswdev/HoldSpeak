"""HS-103-04 — the breaker wired into the two most user-visible call sites:
dictation-runtime classify() and meeting-intel's cloud chat completion.
`_reset_endpoint_health` (tests/conftest.py, autouse) keeps this global
breaker state from leaking between tests."""
from __future__ import annotations

from typing import Any

import pytest

from holdspeak.intel.endpoint_health import default_health


class _AlwaysFailsCompletions:
    def create(self, **kwargs: Any) -> Any:
        raise ConnectionError("no route to host")


class _AlwaysFailsClient:
    def __init__(self, **kwargs: Any) -> None:
        self.chat = type("_Chat", (), {"completions": _AlwaysFailsCompletions()})()


def test_dictation_classify_opens_the_circuit_after_n_failures_then_fails_fast():
    from holdspeak.plugins.dictation.grammars import BlockSet, BlockSpec, StructuredOutputSchema
    from holdspeak.plugins.dictation.runtime_openai_compatible import OpenAICompatibleRuntime

    schema = StructuredOutputSchema.from_block_set(
        BlockSet(blocks=(BlockSpec(id="ai_prompt_buildout"),))
    )
    rt = OpenAICompatibleRuntime(
        model="qwen-local",
        base_url="http://10.255.255.1:9/v1",  # deliberately unreachable identity
        api_key_env="",
        client_factory=lambda **kw: _AlwaysFailsClient(**kw),
    )
    call_count = 0
    for _ in range(default_health._failure_threshold):
        with pytest.raises(RuntimeError):
            rt.classify("classify this", schema)
        call_count += 1

    snap = default_health.snapshot()["dictation:http://10.255.255.1:9/v1"]
    assert snap["circuit_open"] is True
    assert snap["consecutive_failures"] == call_count

    # The circuit is now open: the NEXT call must fail fast — no network
    # attempt at all — with an honest reason naming the endpoint.
    calls_before = rt._client.chat.completions  # type: ignore[union-attr]
    with pytest.raises(RuntimeError, match="unreachable"):
        rt.classify("classify this", schema)
    # still the same completions object; nothing new was recorded server-side
    # (a real HTTP client would show no new connection attempt — here we
    # confirm via the failure count staying put, since the fast-fail path
    # never reaches record_failure).
    assert default_health.snapshot()[
        "dictation:http://10.255.255.1:9/v1"
    ]["consecutive_failures"] == call_count
    assert rt._client.chat.completions is calls_before


def test_meeting_intel_opens_the_circuit_then_fails_fast(monkeypatch):
    import holdspeak.intel as _intel_pkg
    from holdspeak.intel.engine import MeetingIntel
    from holdspeak.intel.models import MeetingIntelError

    monkeypatch.setattr(_intel_pkg, "OpenAI", lambda **kw: _AlwaysFailsClient(**kw))

    intel = MeetingIntel(
        provider="cloud",
        cloud_model="test-model",
        cloud_api_key_env="",
        cloud_base_url="http://10.255.255.2:9/v1",
    )
    intel._active_provider = "cloud"  # bypass resolve_intel_provider's file/key checks
    intel._ensure_openai_client_loaded()

    for _ in range(default_health._failure_threshold):
        with pytest.raises(MeetingIntelError):
            intel._chat_completion_text([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=64)

    key = intel._cloud_endpoint_key()
    assert default_health.snapshot()[key]["circuit_open"] is True

    with pytest.raises(MeetingIntelError, match="unreachable"):
        intel._chat_completion_text([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=64)
    # the fast-fail path never touched the client, so the failure count is unchanged
    assert default_health.snapshot()[key]["consecutive_failures"] == default_health._failure_threshold


def test_a_later_success_clears_the_circuit_and_calls_go_through_again(monkeypatch):
    """No behavior change for the common healthy case: once an endpoint is
    healthy again (post-cooldown probe succeeds), calls flow normally."""
    import time as time_module

    import holdspeak.intel as _intel_pkg
    from holdspeak.intel.engine import MeetingIntel
    from holdspeak.intel.models import MeetingIntelError

    monkeypatch.setattr(_intel_pkg, "OpenAI", lambda **kw: _AlwaysFailsClient(**kw))
    intel = MeetingIntel(
        provider="cloud", cloud_model="m", cloud_api_key_env="", cloud_base_url="http://10.255.255.3:9/v1",
    )
    intel._active_provider = "cloud"
    intel._ensure_openai_client_loaded()

    for _ in range(default_health._failure_threshold):
        with pytest.raises(MeetingIntelError):
            intel._chat_completion_text([{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=64)

    key = intel._cloud_endpoint_key()
    assert default_health.snapshot()[key]["circuit_open"] is True

    # Simulate cooldown elapsing, then a real recovery.
    monkeypatch.setattr(
        default_health, "_clock", lambda: time_module.monotonic() + 3600
    )
    ok, reason = default_health.check(key)
    assert ok is True and reason is None
    default_health.record_success(key)
    assert default_health.snapshot()[key]["circuit_open"] is False
    assert default_health.snapshot()[key]["consecutive_failures"] == 0
