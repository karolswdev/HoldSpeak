"""HS-29-01: the real customer_signal_extractor plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.customer_signal_extractor import (
    CustomerSignalExtractorPlugin,
    _extract_signals,
    _normalize_type,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"signals": [
  {"signal": "Wants CSV export", "type": "feature request", "quote": "I really need CSV"},
  {"signal": "Hates the slow dashboard", "type": "pain", "quote": null},
  {"signal": "Considering a competitor", "type": "churn", "quote": "we might switch"}
]}
```"""


def _plugin(response):
    return CustomerSignalExtractorPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = CustomerSignalExtractorPlugin()
    assert p.id == "customer_signal_extractor"
    assert p.kind == "signals"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_extracts_and_classifies() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "Customer call."})
    assert out["confidence_hint"] == 1.0
    assert [s["type"] for s in out["signals"]] == ["request", "pain", "churn_risk"]
    assert out["signals"][1]["quote"] is None
    assert "3 customer signal(s)" in out["summary"]


def test_run_unknown_type_falls_back_to_request() -> None:
    out = _plugin('{"signals": [{"signal": "X", "type": "weird"}]}').run({"transcript": "t"})
    assert out["signals"][0]["type"] == "request"


def test_run_signal_without_text_dropped() -> None:
    out = _plugin('{"signals": [{"type": "pain"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "signals" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"signals": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "signals" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = CustomerSignalExtractorPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_normalize_type() -> None:
    assert _normalize_type("feature request") == "request"
    assert _normalize_type("complaint") == "pain"
    assert _normalize_type("churn") == "churn_risk"
    assert _normalize_type("compliment") == "praise"
    assert _normalize_type("bogus") == "request"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_signals('{"foo": 1}') is None
    assert _extract_signals("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("customer_signal_extractor"), CustomerSignalExtractorPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "customer_signal_extractor",
        context={"transcript": "signals"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
