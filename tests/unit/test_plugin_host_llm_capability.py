"""HS-16-02: the LLM capability gate.

Covers both halves of the wiring:
- `resolve_llm_capability` decides whether `"llm"` should be enabled, from
  config + a cheap provider-resolution check (non-fatal on error).
- `PluginHost` blocks an `["llm"]`-requiring plugin when the capability is
  absent and runs it when present.
"""

from __future__ import annotations

from types import SimpleNamespace

import holdspeak.intel as intel_module
from holdspeak.intel import resolve_llm_capability
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.host import PluginHost


class _LlmPlugin:
    """Trivial inline plugin with the same capability declaration as mermaid."""

    id = "trivial_llm"
    version = "1.0.0"
    required_capabilities = ["llm"]

    def run(self, context: dict[str, object]) -> dict[str, object]:
        _ = context
        return {"ok": True}


def _meeting(**overrides):
    base = dict(
        intel_enabled=True,
        intel_provider="cloud",
        intel_realtime_model=None,
        intel_cloud_model="Qwen3.5-9B-UD-Q6_K_XL.gguf",
        intel_cloud_api_key_env="OPENAI_API_KEY",
        intel_cloud_base_url="http://192.168.1.43:8080/v1",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


# --- resolve_llm_capability ------------------------------------------------


def test_capability_true_when_provider_resolves(monkeypatch) -> None:
    monkeypatch.setattr(intel_module, "resolve_intel_provider", lambda *a, **k: ("cloud", None))
    assert resolve_llm_capability(_meeting()) is True


def test_capability_false_when_provider_unresolved(monkeypatch) -> None:
    monkeypatch.setattr(intel_module, "resolve_intel_provider", lambda *a, **k: (None, "no provider"))
    assert resolve_llm_capability(_meeting()) is False


def test_capability_false_when_intel_disabled(monkeypatch) -> None:
    # Gated before resolution: the resolver must not even be consulted.
    def _boom(*a, **k):
        raise AssertionError("resolve_intel_provider should not be called")

    monkeypatch.setattr(intel_module, "resolve_intel_provider", _boom)
    assert resolve_llm_capability(_meeting(intel_enabled=False)) is False


def test_capability_false_when_resolution_raises(monkeypatch) -> None:
    def _raise(*a, **k):
        raise RuntimeError("provider blew up")

    monkeypatch.setattr(intel_module, "resolve_intel_provider", _raise)
    # Non-fatal: a broken resolver must not crash host construction.
    assert resolve_llm_capability(_meeting()) is False


# --- PluginHost capability gate --------------------------------------------


def test_host_with_capability_runs_llm_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    host.register(_LlmPlugin())

    result = host.execute(
        "trivial_llm",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "success"
    assert result.output == {"ok": True}


def test_host_without_capability_blocks_llm_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5)  # no capabilities
    host.register(_LlmPlugin())

    result = host.execute(
        "trivial_llm",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"


def test_mermaid_architecture_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)  # no capabilities
    register_builtin_plugins(host)

    result = host.execute(
        "mermaid_architecture",
        context={"transcript": "We use a gateway in front of three services."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"


def test_mermaid_architecture_passes_capability_gate_when_enabled() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)

    result = host.execute(
        "mermaid_architecture",
        context={"transcript": "We use a gateway in front of three services."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    # Deferred plugin → queued (not run inline); the point is it is NOT blocked
    # for a missing capability anymore.
    assert result.status != "blocked"
    assert "Missing capabilities" not in (result.error or "")
