"""HS-27-03: the real decision_capture plugin."""

from __future__ import annotations

import pytest

from holdspeak.plugins.intelligence import PluginProviderFailure
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.decision_capture import (
    DecisionCapturePlugin,
    _extract_decisions,
    _verified_timestamp,
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
    return intel_plugin(DecisionCapturePlugin(), lambda _m, **_kw: response)


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


def test_source_timestamp_window_accepts_end_boundary_and_records_named_drop() -> None:
    segments = [{"text": "Ship Friday", "speaker": "Me", "start_time": 4.0, "end_time": 12.5}]
    response = """```json
{"decisions": [
  {"decision": "Ship Friday", "rationale": null, "source_timestamp": 12.5},
  {"decision": "Invented moment", "rationale": null, "source_timestamp": 12.501}
], "open_questions": []}
```"""

    out = _plugin(response).run({"transcript": "Ship Friday", "transcript_segments": segments})

    assert out["decisions"][0]["source_timestamp"] == 12.5
    assert "source_timestamp" not in out["decisions"][1]
    assert out["provenance_drops"] == [
        {
            "decision": "Invented moment",
            "field": "source_timestamp",
            "rejected_value": 12.501,
            "reason": "source_timestamp_out_of_range",
        }
    ]
    assert _verified_timestamp(4.0, (4.0, 12.5)) == 4.0
    assert _verified_timestamp(12.5, (4.0, 12.5)) == 12.5
    assert _verified_timestamp(3.999, (4.0, 12.5)) is None


def test_timestamp_field_remains_optional_for_golden_output() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We made some calls."})
    assert all("source_timestamp" not in decision for decision in out["decisions"])
    assert "provenance_drops" not in out


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


def test_run_provider_failure_reaches_the_admitted_child() -> None:
    """HS-131-14: a physical failure is the CHILD's outcome, not a summary.

    The plugin used to catch it and return a failure-shaped record, so the
    admitted child earned a `succeeded` receipt for an attempt that failed.
    It is now un-absorbable by `except Exception` and reaches the adapter.
    """
    def _boom(_messages, **_kwargs):
        raise RuntimeError("down")

    bound = intel_plugin(DecisionCapturePlugin(), _boom)
    with pytest.raises(PluginProviderFailure) as failure:
        bound.run({"transcript": "t"})
    assert failure.value.reason == "RuntimeError"


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
