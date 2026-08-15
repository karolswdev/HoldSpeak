"""HS-29-03: the real stakeholder_update_drafter plugin."""

from __future__ import annotations

import pytest

from holdspeak.plugins.intelligence import PluginProviderFailure
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.stakeholder_update_drafter import (
    StakeholderUpdateDrafterPlugin,
    _extract_update,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"headline": "Feedback loop kicks off",
 "highlights": ["Scoped the MVP", "Picked Postgres"],
 "risks": ["Classifier owner undecided"],
 "next_steps": ["Sketch ingestion this week"]}
```"""


def _plugin(response):
    return intel_plugin(StakeholderUpdateDrafterPlugin(), lambda _m, **_kw: response)


def test_attributes() -> None:
    p = StakeholderUpdateDrafterPlugin()
    assert p.id == "stakeholder_update_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_drafts_update() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "kickoff"})
    assert out["confidence_hint"] == 1.0
    u = out["update"]
    assert u["headline"] == "Feedback loop kicks off"
    assert u["highlights"] == ["Scoped the MVP", "Picked Postgres"]
    assert u["risks"] == ["Classifier owner undecided"]
    assert u["next_steps"] == ["Sketch ingestion this week"]
    assert out["summary"] == "Feedback loop kicks off"


def test_run_headline_only_is_success() -> None:
    out = _plugin('{"headline": "All on track", "highlights": [], "risks": [], "next_steps": []}').run(
        {"transcript": "t"}
    )
    assert out["confidence_hint"] == 1.0
    assert out["update"]["headline"] == "All on track"


def test_run_empty_update_is_failure() -> None:
    out = _plugin('{"headline": "", "highlights": [], "risks": [], "next_steps": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "update" not in out


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

    bound = intel_plugin(StakeholderUpdateDrafterPlugin(), _boom)
    with pytest.raises(PluginProviderFailure) as failure:
        bound.run({"transcript": "t"})
    assert failure.value.reason == "RuntimeError"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_update('{"foo": 1}') is None
    assert _extract_update("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("stakeholder_update_drafter"), StakeholderUpdateDrafterPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "stakeholder_update_drafter",
        context={"transcript": "update"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
