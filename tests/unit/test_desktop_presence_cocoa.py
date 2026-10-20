"""C12: native presence projection and parent-side menu command bridge."""

from __future__ import annotations

import queue
import threading

import pytest

from holdspeak.desktop_presence_cocoa import (
    PRESENCE_STATUS_PROBE_JS,
    CocoaPresenceRenderer,
    _build_status_menu,
    _CocoaPresenceUI,
)


def test_status_probe_reads_the_existing_connection_lamp() -> None:
    assert "presence-activity" in PRESENCE_STATUS_PROBE_JS
    assert "data-on" in PRESENCE_STATUS_PROBE_JS
    assert "available" in PRESENCE_STATUS_PROBE_JS


class _FakeMenu:
    def __init__(self) -> None:
        self.autoenables: bool | None = None
        self.items: list[object] = []

    @classmethod
    def alloc(cls):
        return cls()

    def init(self):
        return self

    def setAutoenablesItems_(self, value: bool) -> None:
        self.autoenables = value

    def addItem_(self, item: object) -> None:
        self.items.append(item)


class _FakeMenuItem:
    def __init__(self) -> None:
        self.enabled = True
        self.target = None
        self.title = ""

    @classmethod
    def alloc(cls):
        return cls()

    def initWithTitle_action_keyEquivalent_(self, title, _action, _key):
        self.title = title
        return self

    @staticmethod
    def separatorItem():
        return object()

    def setTarget_(self, target) -> None:
        self.target = target

    def setEnabled_(self, value: bool) -> None:
        self.enabled = value


class _FakeAppKit:
    NSMenu = _FakeMenu
    NSMenuItem = _FakeMenuItem


def test_native_stop_target_is_objc_action_and_menu_stays_runtime_controlled() -> None:
    foundation = pytest.importorskip("Foundation")
    events: queue.Queue[tuple[str, object]] = queue.Queue()
    menu, state_item, stop_item, target = _build_status_menu(_FakeAppKit, events)

    target.stop_(None)

    assert isinstance(target, foundation.NSObject)
    assert target.stop_.selector == b"stop:"
    assert menu.autoenables is False
    assert state_item.enabled is False
    assert stop_item.enabled is False
    assert stop_item.target is target
    assert events.get_nowait() == ("stop", None)


class _FakePanel:
    def __init__(self) -> None:
        self.ordered_out = 0

    def orderOut_(self, _sender) -> None:
        self.ordered_out += 1


class _FakeStateItem:
    def __init__(self) -> None:
        self.title = "Recording · 00:05"

    def setTitle_(self, title: str) -> None:
        self.title = title


class _FakeStopItem:
    def __init__(self) -> None:
        self.enabled = True

    def setEnabled_(self, enabled: bool) -> None:
        self.enabled = enabled


def _bare_ui_for_hide(state: str) -> _CocoaPresenceUI:
    ui = object.__new__(_CocoaPresenceUI)
    ui._activity = {"state": state}
    ui._card_visible = False
    ui._card_seen = False
    ui._panel_shown = True
    ui._last_status_signature = ("Recording · 00:05", True, "#ff6b35")
    ui.panel = _FakePanel()
    ui.status_state_item = _FakeStateItem()
    ui.stop_menu_item = _FakeStopItem()
    ui._set_glyph = lambda _accent: None
    return ui


def test_native_linger_keeps_live_recording_status_but_idle_hide_clears_it() -> None:
    live_ui = _bare_ui_for_hide("meeting_live")
    live_ui.hide(reason="linger_elapsed")
    assert live_ui.status_state_item.title == "Recording · 00:05"
    assert live_ui.stop_menu_item.enabled is True

    idle_ui = _bare_ui_for_hide("idle")
    idle_ui.hide(reason="hidden")
    assert idle_ui.status_state_item.title == "Ready"
    assert idle_ui.stop_menu_item.enabled is False
    assert idle_ui._last_status_signature is None


def test_parent_native_stop_event_invokes_the_runtime_callback() -> None:
    events: queue.Queue[tuple[str, object]] = queue.Queue()
    called = threading.Event()
    renderer = CocoaPresenceRenderer(
        lambda: "http://127.0.0.1:1",
        stop_callback=called.set,
    )
    renderer._events = events
    worker = threading.Thread(target=renderer._consume_events, daemon=True)
    worker.start()
    try:
        events.put(("stop", None))
        assert called.wait(timeout=1.0)
    finally:
        renderer._event_stop.set()
        worker.join(timeout=1.0)



class _FakeStatusButton:
    def __init__(self):
        self.title = ""
        self.tooltip = ""

    def setTitle_(self, title):
        self.title = title

    def setToolTip_(self, tooltip):
        self.tooltip = tooltip


def test_menu_bar_shows_elapsed_recording_and_disconnect_then_clears_idle(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    import holdspeak.desktop_presence as presence

    now = datetime(2026, 10, 19, 12, 5, 8, tzinfo=timezone.utc)
    monkeypatch.setattr(presence, "utc_now", lambda: now)
    ui = _bare_ui_for_hide("meeting_live")
    ui._activity["started_at"] = "2026-10-19T12:00:00+00:00"
    ui._desk_available = True
    ui._last_status_signature = None
    button = _FakeStatusButton()
    ui.status_item = SimpleNamespace(button=lambda: button)
    ui.refresh_status()
    assert button.title == "Recording · 05:08"
    assert button.tooltip == "Recording · 05:08"
    assert ui.stop_menu_item.enabled is True

    ui._desk_available = False
    ui.refresh_status()
    assert button.title == "Desk not running"
    assert ui.stop_menu_item.enabled is False

    ui._desk_available = True
    ui._activity = {"state": "idle"}
    ui.refresh_status()
    assert button.title == ""
    assert ui.stop_menu_item.enabled is False


def test_connection_projection_accepts_native_webkit_dictionary():
    from types import SimpleNamespace
    foundation = pytest.importorskip("Foundation")
    result = foundation.NSDictionary.dictionaryWithObject_forKey_(False, "available")
    observed = []
    ui = object.__new__(_CocoaPresenceUI)
    ui._desk_available = True
    ui.refresh_status = lambda: observed.append(ui._desk_available)
    ui.webview = SimpleNamespace(evaluateJavaScript_completionHandler_=lambda _script, callback: callback(result, None))
    ui.poll_status()
    assert observed == [False]
