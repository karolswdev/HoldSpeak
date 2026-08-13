"""HS-29-02: the real runbook_delta plugin."""

from __future__ import annotations

import pytest

from holdspeak.plugins.intelligence import PluginProviderFailure
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.runbook_delta import (
    RunbookDeltaPlugin,
    _extract_changes,
    _normalize_type,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"changes": [
  {"change": "Flush the CDN cache after deploy", "type": "added", "detail": "step 7"},
  {"change": "Rollback command", "type": "changed", "detail": "use the new script"},
  {"change": "Manual DB toggle", "type": "deleted", "detail": null}
]}
```"""


def _plugin(response):
    return intel_plugin(RunbookDeltaPlugin(), lambda _m, **_kw: response)


def test_attributes() -> None:
    p = RunbookDeltaPlugin()
    assert p.id == "runbook_delta"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_classifies() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "ops retro"})
    assert out["confidence_hint"] == 1.0
    assert [c["type"] for c in out["changes"]] == ["added", "modified", "removed"]
    assert out["changes"][2]["detail"] is None
    assert "3 runbook change(s)" in out["summary"]


def test_run_unknown_type_falls_back_to_modified() -> None:
    out = _plugin('{"changes": [{"change": "X", "type": "weird"}]}').run({"transcript": "t"})
    assert out["changes"][0]["type"] == "modified"


def test_run_change_without_text_dropped() -> None:
    out = _plugin('{"changes": [{"type": "added"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "changes" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"changes": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "changes" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


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

    bound = intel_plugin(RunbookDeltaPlugin(), _boom)
    with pytest.raises(PluginProviderFailure) as failure:
        bound.run({"transcript": "t"})
    assert failure.value.reason == "RuntimeError"


def test_normalize_type() -> None:
    assert _normalize_type("add") == "added"
    assert _normalize_type("changed") == "modified"
    assert _normalize_type("deleted") == "removed"
    assert _normalize_type("bogus") == "modified"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_changes('{"foo": 1}') is None
    assert _extract_changes("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("runbook_delta"), RunbookDeltaPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "runbook_delta",
        context={"transcript": "ops"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
