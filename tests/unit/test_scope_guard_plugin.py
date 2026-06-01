"""HS-29-01: the real scope_guard plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.scope_guard import (
    ScopeGuardPlugin,
    _extract_findings,
    _normalize_verdict,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"findings": [
  {"item": "PDF export", "verdict": "in_scope", "rationale": "agreed in kickoff"},
  {"item": "Live chat", "verdict": "scope creep", "rationale": "new ask, no decision"},
  {"item": "SSO", "verdict": "deferred", "rationale": null}
]}
```"""


def _plugin(response):
    return ScopeGuardPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = ScopeGuardPlugin()
    assert p.id == "scope_guard"
    assert p.kind == "validator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_classifies() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We reviewed scope."})
    assert out["confidence_hint"] == 1.0
    assert [f["verdict"] for f in out["findings"]] == ["in_scope", "scope_creep", "out_of_scope"]
    assert out["findings"][2]["rationale"] is None
    assert "1 flagged as scope creep" in out["summary"]


def test_run_unknown_verdict_falls_back_to_in_scope() -> None:
    out = _plugin('{"findings": [{"item": "X", "verdict": "weird"}]}').run({"transcript": "t"})
    assert out["findings"][0]["verdict"] == "in_scope"


def test_run_finding_without_item_dropped() -> None:
    out = _plugin('{"findings": [{"verdict": "in_scope"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "findings" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"findings": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "findings" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = ScopeGuardPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_normalize_verdict() -> None:
    assert _normalize_verdict("scope creep") == "scope_creep"
    assert _normalize_verdict("deferred") == "out_of_scope"
    assert _normalize_verdict("included") == "in_scope"
    assert _normalize_verdict("bogus") == "in_scope"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_findings('{"foo": 1}') is None
    assert _extract_findings("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("scope_guard"), ScopeGuardPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "scope_guard",
        context={"transcript": "scope"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
