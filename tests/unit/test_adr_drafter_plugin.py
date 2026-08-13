"""HS-28-02: the real adr_drafter plugin."""

from __future__ import annotations

import pytest

from holdspeak.plugins.intelligence import PluginProviderFailure
from tests.unit.plugin_dispatch_rig import intel_plugin
from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.adr_drafter import (
    AdrDrafterPlugin,
    _extract_adrs,
    _normalize_status,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"adrs": [
  {"title": "Use Postgres for billing", "status": "accepted",
   "context": "Need transactional integrity for invoices",
   "decision": "Adopt Postgres over DynamoDB",
   "consequences": "Ops must run a managed Postgres"},
  {"title": "Async notifications via a queue", "status": "proposed",
   "context": "Spiky notification load", "decision": "Introduce a Redis queue",
   "consequences": "New infra dependency"}
]}
```"""


def _plugin(response):
    return intel_plugin(AdrDrafterPlugin(), lambda _m, **_kw: response)


def test_attributes() -> None:
    p = AdrDrafterPlugin()
    assert p.id == "adr_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_drafts_adrs() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We settled the data store."})
    assert out["confidence_hint"] == 1.0
    assert [a["title"] for a in out["adrs"]] == [
        "Use Postgres for billing",
        "Async notifications via a queue",
    ]
    assert out["adrs"][0]["status"] == "accepted"
    assert out["adrs"][1]["status"] == "proposed"
    assert "2 ADR(s)" in out["summary"]
    assert "1 accepted" in out["summary"]


def test_run_status_synonym_coerced() -> None:
    out = _plugin(
        '{"adrs": [{"title": "X", "status": "approved", "decision": "do X"}]}'
    ).run({"transcript": "t"})
    assert out["adrs"][0]["status"] == "accepted"


def test_run_unknown_status_falls_back_to_proposed() -> None:
    out = _plugin(
        '{"adrs": [{"title": "X", "status": "weird", "decision": "do X"}]}'
    ).run({"transcript": "t"})
    assert out["adrs"][0]["status"] == "proposed"


def test_run_adr_without_decision_is_dropped() -> None:
    # Title but no decision → not a meaningful ADR → dropped → empty → failure.
    out = _plugin('{"adrs": [{"title": "X", "context": "c"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "adrs" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"adrs": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "adrs" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("just chatter, no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "adrs" not in out


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

    bound = intel_plugin(AdrDrafterPlugin(), _boom)
    with pytest.raises(PluginProviderFailure) as failure:
        bound.run({"transcript": "t"})
    assert failure.value.reason == "RuntimeError"


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_adrs('{"foo": 1}') is None
    assert _extract_adrs("") is None
    assert _extract_adrs("[1,2,3]") is None


def test_normalize_status() -> None:
    assert _normalize_status("Accepted") == "accepted"
    assert _normalize_status("agreed") == "accepted"
    assert _normalize_status("draft") == "proposed"
    assert _normalize_status("obsolete") == "deprecated"
    assert _normalize_status(None) == "proposed"


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("adr_drafter"), AdrDrafterPlugin)


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "adr_drafter",
        context={"transcript": "We decided on the data store."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
