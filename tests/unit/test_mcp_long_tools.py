"""Every name in ``holdspeak/mcp/long_tools.py`` is a real MCP tool (a typo would silently queue it)."""
from __future__ import annotations

from holdspeak.mcp.long_tools import LONG_TOOLS
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY


def test_every_long_tool_is_a_real_tool() -> None:
    assert set(LONG_TOOLS) - set(TOOL_AUTHORITY) == set()
    assert all(reason for reason in LONG_TOOLS.values())


def test_lock_keys_name_the_objects_and_the_one_provider_key() -> None:
    from holdspeak.mcp.long_tools import lock_keys

    assert lock_keys("project.watch.test", {"watch_id": "w1"}) == ["providers", "watch_id=w1"]
    assert lock_keys("project.watch.set_rules", {"watch_id": "w1", "rules": []}) == ["watch_id=w1"]
    assert lock_keys("project.draft_update", {"project_id": "p", "command_id": "c"}) == [
        "command_id=c", "project_id=p"]
    assert lock_keys("provider.jira_search", {"connection_ref": "a|b", "jql": "x"}) == ["providers"]
    assert lock_keys("desk.list", {"kind": "notes"}) == []


def test_tools_whose_overlap_was_not_proved_safe_stay_in_the_ordered_queue() -> None:
    for name in ("project.open_review", "watch.refresh", "reaction.process", "heartbeat.run_now",
                 "concierge.detect", "concierge.probe", "concierge.download", "model_library.download"):
        assert name not in LONG_TOOLS, name
