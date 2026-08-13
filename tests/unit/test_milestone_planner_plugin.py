"""HS-28-03: the real milestone_planner plugin."""

from __future__ import annotations

import pytest

from holdspeak.plugins.intelligence import PluginProviderFailure
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.milestone_planner import (
    MilestonePlannerPlugin,
    _extract_milestones,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"milestones": [
  {"name": "Beta launch", "target": "Q3",
   "deliverables": ["Auth", "Billing"], "dependencies": ["API freeze"]},
  {"name": "GA", "target": null, "deliverables": [], "dependencies": ["Beta launch"]}
]}
```"""


def _plugin(response):
    return intel_plugin(MilestonePlannerPlugin(), lambda _m, **_kw: response)


def test_attributes() -> None:
    p = MilestonePlannerPlugin()
    assert p.id == "milestone_planner"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_extracts_milestones() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We planned the roadmap."})
    assert out["confidence_hint"] == 1.0
    assert [m["name"] for m in out["milestones"]] == ["Beta launch", "GA"]
    assert out["milestones"][0]["target"] == "Q3"
    assert out["milestones"][0]["deliverables"] == ["Auth", "Billing"]
    assert out["milestones"][1]["target"] is None
    assert out["milestones"][1]["dependencies"] == ["Beta launch"]
    assert "2 milestone(s)" in out["summary"]
    assert "1 with a target date" in out["summary"]


def test_run_missing_target_is_null() -> None:
    out = _plugin('{"milestones": [{"name": "MVP", "target": "TBD"}]}').run({"transcript": "t"})
    assert out["milestones"][0]["target"] is None
    assert out["milestones"][0]["deliverables"] == []


def test_run_milestone_without_name_dropped() -> None:
    out = _plugin('{"milestones": [{"target": "Q4"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "milestones" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"milestones": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "milestones" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json here").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "milestones" not in out


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

    bound = intel_plugin(MilestonePlannerPlugin(), _boom)
    with pytest.raises(PluginProviderFailure) as failure:
        bound.run({"transcript": "t"})
    assert failure.value.reason == "RuntimeError"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_milestones('{"foo": 1}') is None
    assert _extract_milestones("") is None
    assert _extract_milestones("[1,2,3]") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("milestone_planner"), MilestonePlannerPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "milestone_planner",
        context={"transcript": "We planned milestones."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
