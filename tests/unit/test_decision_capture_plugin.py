"""HS-27-03: the real decision_capture plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.decision_capture import (
    DecisionCapturePlugin,
    _extract_decisions,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"decisions": [
  {"decision": "Adopt the new API gateway", "rationale": "Centralizes auth"},
  {"decision": "Use Postgres for billing", "rationale": null}
],
 "open_questions": ["Who owns the migration?", "What is the rollout date?"]}
```"""


def _plugin(response):
    return DecisionCapturePlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = DecisionCapturePlugin()
    assert p.id == "decision_capture"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_captures_decisions_and_questions() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We made some calls."})
    assert out["confidence_hint"] == 1.0
    assert [d["decision"] for d in out["decisions"]] == [
        "Adopt the new API gateway",
        "Use Postgres for billing",
    ]
    assert out["decisions"][0]["rationale"] == "Centralizes auth"
    assert out["decisions"][1]["rationale"] is None
    assert out["open_questions"] == ["Who owns the migration?", "What is the rollout date?"]
    assert "2 decision(s); 2 open question(s)" in out["summary"]


def test_run_decisions_only_is_success() -> None:
    out = _plugin('{"decisions": ["Ship on Friday"], "open_questions": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 1.0
    assert out["decisions"] == [{"decision": "Ship on Friday", "rationale": None}]
    assert out["open_questions"] == []


def test_run_empty_is_failure() -> None:
    out = _plugin('{"decisions": [], "open_questions": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "decisions" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json here, just chatter").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "decisions" not in out


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = DecisionCapturePlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_keys() -> None:
    assert _extract_decisions('{"foo": 1}') is None
    assert _extract_decisions("") is None
    assert _extract_decisions("[1,2,3]") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("decision_capture"), DecisionCapturePlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "decision_capture",
        context={"transcript": "We decided things."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
