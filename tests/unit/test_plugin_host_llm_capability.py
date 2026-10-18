"""HS-16-02: the LLM capability gate.

Covers both halves of the wiring:
- `resolve_llm_capability` decides whether `"llm"` should be enabled, from
  the "Meeting summaries" route in Engines (non-fatal on error; Capture C4).
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
# Capture C4: the capability follows the "Meeting summaries" route in Engines
# (``project_route``), never the old ``meeting.intel_provider`` setting.


def _route(monkeypatch, answer) -> list[object]:
    seen: list[object] = []

    def _project(db, **_kwargs):
        seen.append(db)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(
        "holdspeak.services.meeting_route_projection.project_route", _project
    )
    return seen


def test_capability_true_when_the_summary_route_is_ready(monkeypatch) -> None:
    seen = _route(monkeypatch, {"status": "ready", "legs": [{"host": "192.168.1.43"}]})
    db = object()
    assert resolve_llm_capability(_meeting(), db=db) is True
    assert seen == [db]


def test_capability_false_when_the_summary_route_is_unavailable(monkeypatch) -> None:
    _route(monkeypatch, {"status": "unavailable", "reason_code": "no assignment", "legs": []})
    assert resolve_llm_capability(_meeting(), db=object()) is False


def test_capability_ignores_the_old_provider_setting(monkeypatch) -> None:
    # The old config resolver says yes; with no engine in Engines the answer is no.
    monkeypatch.setattr(intel_module, "resolve_intel_provider", lambda *a, **k: ("cloud", None))
    _route(monkeypatch, {"status": "unavailable", "reason_code": "no assignment", "legs": []})
    assert resolve_llm_capability(_meeting(), db=object()) is False


def test_capability_false_when_intel_disabled(monkeypatch) -> None:
    # Gated before resolution: the route must not even be read.
    _route(monkeypatch, AssertionError("project_route should not be called"))
    assert resolve_llm_capability(_meeting(intel_enabled=False), db=object()) is False


def test_capability_false_when_resolution_raises(monkeypatch) -> None:
    _route(monkeypatch, RuntimeError("route read blew up"))
    # Non-fatal: a broken read must not crash host construction.
    assert resolve_llm_capability(_meeting(), db=object()) is False


# --- PluginHost capability gate --------------------------------------------


def test_host_with_capability_and_an_admitted_handle_runs_llm_plugin() -> None:
    """HS-131-14: the capability gate now has TWO halves.

    `enabled_capabilities` says the deployment CAN do model work; the admitted
    dispatch handle says THIS run may. A plugin that declares `llm` and is handed
    no handle refuses by name rather than resolving a provider of its own — see
    the test below.
    """
    from tests.unit.plugin_dispatch_rig import admitted_dispatch

    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    host.register(_LlmPlugin())
    dispatch, _engine, _context = admitted_dispatch("{}")

    result = host.execute(
        "trivial_llm",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
        dispatch=dispatch,
    )

    assert result.status == "success"
    assert result.output == {"ok": True}


def test_host_with_capability_but_no_admitted_handle_refuses_by_name() -> None:
    from holdspeak.plugins.intelligence import PLUGIN_DISPATCH_REQUIRED

    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    host.register(_LlmPlugin())

    result = host.execute(
        "trivial_llm",
        context={},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )

    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)


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
