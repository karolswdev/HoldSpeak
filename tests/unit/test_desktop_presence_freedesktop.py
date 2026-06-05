"""HS-41-05: Linux freedesktop presence renderer (notification + tray).

Logic is tested with injected fake seams (no gi/libnotify needed), so it runs on
any platform. The real libnotify/AppIndicator wrappers are exercised on Linux.
"""

from __future__ import annotations

import holdspeak.desktop_presence as dp
from holdspeak.desktop_presence import build_presence_window_view
from holdspeak.desktop_presence_freedesktop import (
    FreedesktopPresenceRenderer,
    notification_for_view,
)
from holdspeak.runtime_activity import RuntimeActivityTracker


class FakeNotifier:
    def __init__(self) -> None:
        self.specs: list[dict] = []
        self.closed = 0

    def notify(self, spec: dict) -> None:
        self.specs.append(spec)

    def close(self) -> None:
        self.closed += 1


class FakeTray:
    def __init__(self) -> None:
        self.states: list[str] = []
        self.idled = 0
        self.closed = 0

    def set_state(self, view) -> None:
        self.states.append(view.state)

    def set_idle(self) -> None:
        self.idled += 1

    def close(self) -> None:
        self.closed += 1


def _renderer():
    notifier, tray = FakeNotifier(), FakeTray()
    r = FreedesktopPresenceRenderer(lambda: "http://127.0.0.1:9", notifier=notifier, tray=tray)
    return r, notifier, tray


# ── notification_for_view (pure) ──────────────────────────────────────


def test_notification_for_view_maps_fields() -> None:
    activity = RuntimeActivityTracker().update(
        "recording", source="hotkey", detail="HoldSpeak is listening."
    )
    spec = notification_for_view(build_presence_window_view(activity))
    assert spec["summary"] == "HoldSpeak — Recording"
    assert spec["body"] == "HoldSpeak is listening."
    assert spec["icon"] == "audio-input-microphone"
    assert spec["urgency"] == 1
    assert spec["transient"] is True


def test_notification_error_is_critical_and_persistent() -> None:
    activity = RuntimeActivityTracker().update(
        "error", source="dictation", last_error="Typing failed."
    )
    spec = notification_for_view(build_presence_window_view(activity))
    assert spec["urgency"] == 2
    assert spec["transient"] is False
    assert spec["icon"] == "dialog-error"


# ── Renderer behavior (with fakes) ────────────────────────────────────


def test_renderer_notifies_and_sets_tray_on_show() -> None:
    r, notifier, tray = _renderer()
    tracker = RuntimeActivityTracker()
    r.show(tracker.update("recording", source="hotkey"))
    assert tray.states == ["recording"]
    assert len(notifier.specs) == 1
    assert notifier.specs[0]["summary"] == "HoldSpeak — Recording"


def test_renderer_coalesces_same_state() -> None:
    # Same-state updates refresh the tray but don't re-notify (no spam).
    r, notifier, tray = _renderer()
    tracker = RuntimeActivityTracker()
    r.show(tracker.update("recording", source="hotkey"))
    r.update(tracker.update("recording", source="hotkey", detail="still going"))
    assert len(notifier.specs) == 1            # only one notification
    assert tray.states == ["recording", "recording"]  # tray still refreshed


def test_renderer_notifies_again_on_state_change() -> None:
    r, notifier, tray = _renderer()
    tracker = RuntimeActivityTracker()
    r.show(tracker.update("recording", source="hotkey"))
    r.update(tracker.update("transcribing", source="hotkey"))
    assert [s["summary"] for s in notifier.specs] == [
        "HoldSpeak — Recording",
        "HoldSpeak — Transcribing",
    ]


def test_renderer_hide_idles_tray_and_closes_notification() -> None:
    r, notifier, tray = _renderer()
    tracker = RuntimeActivityTracker()
    r.show(tracker.update("recording", source="hotkey"))
    r.hide(reason="linger_elapsed")
    assert tray.idled == 1
    assert notifier.closed == 1
    # After hide, the next show re-notifies (state was reset).
    r.show(tracker.update("recording", source="hotkey"))
    assert len(notifier.specs) == 2


# ── Selection / availability ──────────────────────────────────────────


def test_select_linux_renderer_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.desktop_presence_freedesktop.freedesktop_presence_available",
        lambda: True,
    )
    picked = dp._select_presence_renderer(
        {"os": "linux", "overlay_capable": False}, lambda: "http://x"
    )
    assert isinstance(picked, FreedesktopPresenceRenderer)


def test_select_linux_renderer_none_without_libnotify(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.desktop_presence_freedesktop.freedesktop_presence_available",
        lambda: False,
    )
    assert dp._select_presence_renderer({"os": "linux"}, lambda: "http://x") is None
