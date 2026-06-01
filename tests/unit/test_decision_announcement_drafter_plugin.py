"""HS-29-03: the real decision_announcement_drafter plugin (the last stub)."""

from __future__ import annotations

from holdspeak.plugins.builtin import (
    DeterministicPlugin,
    register_builtin_plugins,
)
from holdspeak.plugins.builtin import _BUILTIN_PLUGIN_DEFS
from holdspeak.plugins.builtin.decision_announcement_drafter import (
    DecisionAnnouncementDrafterPlugin,
    _extract_announcements,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """```json
{"announcements": [
  {"title": "We're adopting Postgres for billing", "audience": "Engineering",
   "message": "We've decided to use Postgres for billing for ACID guarantees."},
  {"title": "Beta ships in Q3", "audience": null, "message": "Private beta targets Q3."}
]}
```"""


def _plugin(response):
    return DecisionAnnouncementDrafterPlugin(intel_call=lambda _m: response)


def test_attributes() -> None:
    p = DecisionAnnouncementDrafterPlugin()
    assert p.id == "decision_announcement_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_drafts_announcements() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "decisions"})
    assert out["confidence_hint"] == 1.0
    assert [a["title"] for a in out["announcements"]] == [
        "We're adopting Postgres for billing",
        "Beta ships in Q3",
    ]
    assert out["announcements"][0]["audience"] == "Engineering"
    assert out["announcements"][1]["audience"] is None
    assert "2 decision announcement(s)" in out["summary"]


def test_run_announcement_without_message_dropped() -> None:
    out = _plugin('{"announcements": [{"title": "X"}]}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "announcements" not in out


def test_run_empty_is_failure() -> None:
    out = _plugin('{"announcements": []}').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "announcements" not in out


def test_run_unparseable_is_failure() -> None:
    out = _plugin("no json").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "  "})
    assert out["confidence_hint"] == 0.0


def test_run_provider_exception_is_caught() -> None:
    def _boom(_m):
        raise RuntimeError("down")

    out = DecisionAnnouncementDrafterPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_returns_none_without_recognizable_key() -> None:
    assert _extract_announcements('{"foo": 1}') is None
    assert _extract_announcements("") is None


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("decision_announcement_drafter"), DecisionAnnouncementDrafterPlugin)


def test_no_deterministic_stub_remains() -> None:
    """Phase-29 completion: every registered built-in plugin is now real."""
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    registered = register_builtin_plugins(host)
    assert len(registered) == len(_BUILTIN_PLUGIN_DEFS)
    for plugin_id, _kind in _BUILTIN_PLUGIN_DEFS:
        plugin = host.get_plugin(plugin_id)
        assert plugin is not None, plugin_id
        assert not isinstance(plugin, DeterministicPlugin), f"{plugin_id} is still a stub"


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)
    register_builtin_plugins(host)
    result = host.execute(
        "decision_announcement_drafter",
        context={"transcript": "decisions"},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"
