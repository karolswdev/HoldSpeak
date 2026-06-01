"""HS-28-04: the real risk_heatmap plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.risk_heatmap import (
    RiskHeatmapPlugin,
    _extract_risks,
    _normalize_level,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"risks": [
  {"risk": "Vendor may slip the API delivery", "impact": "high",
   "likelihood": "medium", "mitigation": "Build a stub fallback", "owner": "Karol"},
  {"risk": "Migration could lose data", "impact": "critical",
   "likelihood": "low", "mitigation": null, "owner": null}
]}
```"""


def _plugin(response):
    return RiskHeatmapPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = RiskHeatmapPlugin()
    assert p.id == "risk_heatmap"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_builds_register() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We surfaced risks."})
    assert out["confidence_hint"] == 1.0
    assert [r["risk"] for r in out["risks"]] == [
        "Vendor may slip the API delivery",
        "Migration could lose data",
    ]
    assert out["risks"][0]["impact"] == "high"
    assert out["risks"][0]["owner"] == "Karol"
    # "critical" coerces to "high".
    assert out["risks"][1]["impact"] == "high"
    assert out["risks"][1]["mitigation"] is None
    assert out["risks"][1]["owner"] is None
    assert "2 risk(s)" in out["summary"]
    assert "2 high-impact" in out["summary"]


def test_run_unknown_level_coerces_to_medium() -> None:
    out = _plugin(
        '{"risks": [{"risk": "X", "impact": "weird", "likelihood": "huh"}]}'
    ).run({"transcript": "t"})
    assert out["risks"][0]["impact"] == "medium"
    assert out["risks"][0]["likelihood"] == "medium"


def test_run_risk_without_text_dropped() -> None:
    out = _plugin('{"risks": [{"impact": "high"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "risks" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"risks": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "risks" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "risks" not in out


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = RiskHeatmapPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_risks('{"foo": 1}') is None
    assert _extract_risks("") is None
    assert _extract_risks("[1,2,3]") is None


def test_normalize_level() -> None:
    assert _normalize_level("High") == "high"
    assert _normalize_level("critical") == "high"
    assert _normalize_level("moderate") == "medium"
    assert _normalize_level("unlikely") == "low"
    assert _normalize_level("bogus") == "medium"


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("risk_heatmap"), RiskHeatmapPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "risk_heatmap",
        context={"transcript": "We discussed risks."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
