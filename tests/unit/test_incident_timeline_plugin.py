"""HS-29-02: the real incident_timeline plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.incident_timeline import (
    IncidentTimelinePlugin,
    _extract_events,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"events": [
  {"time": "09:02", "event": "Alerts fired for elevated 5xx"},
  {"time": "T+8m", "event": "Rolled back the bad deploy"},
  {"time": null, "event": "Confirmed recovery"}
]}
```"""


def _plugin(response):
    return IncidentTimelinePlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = IncidentTimelinePlugin()
    assert p.id == "incident_timeline"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_preserves_order() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "incident retro"})
    assert out["confidence_hint"] == 1.0
    assert [e["event"] for e in out["events"]] == [
        "Alerts fired for elevated 5xx",
        "Rolled back the bad deploy",
        "Confirmed recovery",
    ]
    assert out["events"][0]["time"] == "09:02"
    assert out["events"][2]["time"] is None
    assert "3 timeline event(s)" in out["summary"]


def test_run_accepts_bare_strings() -> None:
    out = _plugin('{"events": ["Pager fired", "Mitigated"]}').run({"transcript": "t"})
    assert [e["event"] for e in out["events"]] == ["Pager fired", "Mitigated"]
    assert out["events"][0]["time"] is None


def test_run_empty_is_failure() -> None:
    out = _plugin('{"events": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "events" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = IncidentTimelinePlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_events('{"foo": 1}') is None
    assert _extract_events("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("incident_timeline"), IncidentTimelinePlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "incident_timeline",
        context={"transcript": "incident"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
