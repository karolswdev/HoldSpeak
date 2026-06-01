"""HS-27-01: the real action_owner_enforcer plugin."""

from __future__ import annotations

from holdspeak.plugins.builtin import register_builtin_plugins
from holdspeak.plugins.builtin.action_owner_enforcer import (
    ActionOwnerEnforcerPlugin,
    _extract_action_items,
)
from holdspeak.plugins.host import PluginHost

_GOOD_JSON = """Here are the action items:
```json
{"action_items": [
  {"task": "Draft the OAuth flow", "owner": "Karol", "due": "Friday"},
  {"task": "Review the migration plan", "owner": null, "due": null},
  {"task": "Book the venue", "owner": "Sam", "due": null}
]}
```
"""


def _plugin(response):
    return ActionOwnerEnforcerPlugin(intel_call=lambda _messages: response)


def test_attributes() -> None:
    p = ActionOwnerEnforcerPlugin()
    assert p.id == "action_owner_enforcer"
    assert p.kind == "validator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


def test_run_success_flags_gaps() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "We agreed on several tasks."})
    assert out["confidence_hint"] == 1.0
    items = out["action_items"]
    assert [i["task"] for i in items] == [
        "Draft the OAuth flow",
        "Review the migration plan",
        "Book the venue",
    ]
    assert items[0]["gap"] is None
    assert items[1]["gap"] == "missing_both"
    assert items[2]["gap"] == "missing_due"
    assert out["gap_count"] == 2
    assert "2 missing" in out["summary"]


def test_run_parses_bare_json_without_fence() -> None:
    out = _plugin('{"action_items": [{"task": "Ship it", "owner": "Me", "due": "today"}]}').run(
        {"transcript": "t"}
    )
    assert out["confidence_hint"] == 1.0
    assert out["action_items"][0]["gap"] is None
    assert out["gap_count"] == 0


def test_run_unparseable_response_is_clean_failure() -> None:
    out = _plugin("I could not find any structured output here, sorry.").run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "action_items" not in out


def test_run_empty_list_is_failure() -> None:
    out = _plugin('```json\n{"action_items": []}\n```').run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "action_items" not in out


def test_run_no_transcript_is_failure() -> None:
    out = _plugin(_GOOD_JSON).run({"transcript": "   "})
    assert out["confidence_hint"] == 0.0
    assert "action_items" not in out


def test_run_provider_exception_is_caught() -> None:
    def _boom(_messages):
        raise RuntimeError("provider down")

    out = ActionOwnerEnforcerPlugin(intel_call=_boom).run({"transcript": "t"})
    assert out["confidence_hint"] == 0.0
    assert "intel call failed" in out["summary"]


def test_extract_treats_placeholder_owners_as_missing() -> None:
    items = _extract_action_items(
        '{"action_items": [{"task": "X", "owner": "unassigned", "due": "TBD"}]}'
    )
    assert items == [{"task": "X", "owner": None, "due": None, "gap": "missing_both"}]


def test_extract_returns_none_for_non_object() -> None:
    assert _extract_action_items("[1, 2, 3]") is None
    assert _extract_action_items("") is None


def test_host_blocks_without_llm_capability() -> None:
    host = PluginHost(default_timeout_seconds=0.5)  # no capabilities
    register_builtin_plugins(host)
    result = host.execute(
        "action_owner_enforcer",
        context={"transcript": "We will do things."},
        meeting_id="m-1",
        window_id="w-1",
        transcript_hash="abc",
    )
    assert result.status == "blocked"
    assert result.error == "Missing capabilities: llm"


def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("action_owner_enforcer"), ActionOwnerEnforcerPlugin)
