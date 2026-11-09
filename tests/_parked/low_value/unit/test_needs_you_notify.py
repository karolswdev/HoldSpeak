# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_needs_you_notify.py to restore.

# ruff: noqa


# --- TestNeedsYouCache::test_sweep_id_propagated: P1: passes sweep_id=sweep-42 in and reads sweep-42 back
# (was a method of class TestNeedsYouCache)
def test_sweep_id_propagated(self):
    from holdspeak.services.needs_you_aggregate import NeedsYouCache

    builder, _ = self._make_builder()
    cache = NeedsYouCache(builder, max_age_s=60.0)

    cache.invalidate(sweep_id="sweep-42")
    result = cache.get()
    assert result["sweepId"] == "sweep-42"


# --- TestCocoaRendererNotifyCommand::test_notify_command_sent_to_queue: P7/P6: asserts a mock queue.put was called once; asserts a tool name is in the catalogue (the dispatch test beside it calls it)
# (was a method of class TestCocoaRendererNotifyCommand)
def test_notify_command_sent_to_queue(self, monkeypatch):
    from holdspeak.desktop_notify import _notify_cocoa_child

    mock_renderer = MagicMock()
    mock_renderer._commands = MagicMock()
    monkeypatch.setenv("HOLDSPEAK_DESKTOP_NOTIFY", "1")
    result = _notify_cocoa_child(mock_renderer, "Test", "Body", click_url="http://localhost")
    assert result is True
    mock_renderer._commands.put.assert_called_once()
    cmd, payload = mock_renderer._commands.put.call_args[0][0]
    assert cmd == "notify"
    assert payload["title"] == "Test"
    assert payload["body"] == "Body"


# --- TestMCPNotifyTest::test_tool_schema_present: P7/P6: asserts a mock queue.put was called once; asserts a tool name is in the catalogue (the dispatch test beside it calls it)
# (was a method of class TestMCPNotifyTest)
def test_tool_schema_present(self):
    from holdspeak.mcp.families.heartbeat import TOOLS

    names = [t["name"] for t in TOOLS]
    assert "heartbeat.notify_test" in names
