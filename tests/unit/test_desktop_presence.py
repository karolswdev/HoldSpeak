from __future__ import annotations

import pytest

from holdspeak.desktop_presence import (
    DesktopPresenceHost,
    build_desktop_presence_host,
    build_presence_window_view,
    desktop_presence_enabled,
)
from holdspeak.runtime_activity import RuntimeActivityTracker


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def show(self, activity: dict[str, object]) -> None:
        self.calls.append(("show", activity["state"]))

    def update(self, activity: dict[str, object]) -> None:
        self.calls.append(("update", activity["state"]))

    def hide(self, *, reason: str = "") -> None:
        self.calls.append(("hide", reason))

    def close(self) -> None:
        self.calls.append(("close", ""))


class FakeTimer:
    def __init__(self, callback) -> None:
        self.callback = callback
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if not self.cancelled:
            self.callback()


def test_desktop_presence_host_shows_updates_lingers_then_hides() -> None:
    renderer = FakeRenderer()
    timers: list[FakeTimer] = []

    def timer_factory(_delay: float, callback):
        timer = FakeTimer(callback)
        timers.append(timer)
        return timer

    tracker = RuntimeActivityTracker()
    host = DesktopPresenceHost(renderer, timer_factory=timer_factory)

    host.handle_activity(tracker.update("recording", source="hotkey"))
    host.handle_activity(tracker.update("transcribing", source="hotkey"))
    host.handle_activity(tracker.update("complete", source="dictation", label="Typed"))

    assert renderer.calls == [
        ("show", "recording"),
        ("update", "transcribing"),
        ("update", "complete"),
    ]
    assert host.visible is True
    assert len(timers) == 1

    timers[0].fire()

    assert renderer.calls[-1] == ("hide", "linger_elapsed")
    assert host.visible is False


def test_desktop_presence_host_idle_hides_without_linger() -> None:
    renderer = FakeRenderer()
    tracker = RuntimeActivityTracker()
    host = DesktopPresenceHost(renderer, timer_factory=lambda _delay, callback: FakeTimer(callback))

    host.handle_activity(tracker.update("recording", source="hotkey"))
    host.handle_activity(tracker.update("idle", source="hotkey"))

    assert renderer.calls == [("show", "recording"), ("hide", "hidden")]
    assert host.visible is False


def test_desktop_presence_host_cancels_linger_when_new_activity_arrives() -> None:
    renderer = FakeRenderer()
    timers: list[FakeTimer] = []

    def timer_factory(_delay: float, callback):
        timer = FakeTimer(callback)
        timers.append(timer)
        return timer

    tracker = RuntimeActivityTracker()
    host = DesktopPresenceHost(renderer, timer_factory=timer_factory)

    host.handle_activity(tracker.update("recording", source="hotkey"))
    host.handle_activity(tracker.update("complete", source="dictation"))
    host.handle_activity(tracker.update("recording", source="hotkey"))

    assert len(timers) == 1
    assert timers[0].cancelled is True
    timers[0].fire()

    assert renderer.calls == [
        ("show", "recording"),
        ("update", "complete"),
        ("update", "recording"),
    ]
    assert host.visible is True


def test_desktop_presence_enabled_env() -> None:
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "1"}) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "true"}) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "0"}) is False
    assert desktop_presence_enabled({}) is False


def test_build_desktop_presence_host_falls_back_when_renderer_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenRenderer:
        def __init__(self) -> None:
            raise RuntimeError("no gui")

    monkeypatch.setenv("HOLDSPEAK_DESKTOP_PRESENCE", "1")
    monkeypatch.setattr("holdspeak.desktop_presence.TkPresenceRenderer", BrokenRenderer)

    assert build_desktop_presence_host() is None


def test_presence_window_view_maps_state_to_renderer_metadata() -> None:
    tracker = RuntimeActivityTracker()
    activity = tracker.update(
        "recording",
        source="hotkey",
        detail="HoldSpeak is listening.",
        last_event="dictation_recording_started",
    )

    view = build_presence_window_view(activity)

    assert view.visible is True
    assert view.mode == "active"
    assert view.tone == "recording"
    assert view.label == "Recording"
    assert view.detail == "HoldSpeak is listening."
    assert view.event == "dictation_recording_started"
    assert view.accent == "#ff6b35"
    assert view.width == 392
    assert view.min_height == 112


def test_presence_window_view_hides_idle() -> None:
    tracker = RuntimeActivityTracker()
    view = build_presence_window_view(tracker.snapshot())

    assert view.state == "idle"
    assert view.visible is False
    assert view.mode == "hidden"


@pytest.mark.parametrize(
    ("state", "expected_mode", "expected_visible", "expected_tone"),
    [
        ("idle", "hidden", False, "neutral"),
        ("listening", "active", True, "recording"),
        ("recording", "active", True, "recording"),
        ("transcribing", "active", True, "working"),
        ("processing", "active", True, "working"),
        ("typing", "active", True, "working"),
        ("complete", "linger", True, "complete"),
        ("meeting_live", "linger", True, "recording"),
        ("saving", "active", True, "working"),
        ("error", "linger", True, "error"),
    ],
)
def test_presence_window_view_covers_runtime_activity_states(
    state: str,
    expected_mode: str,
    expected_visible: bool,
    expected_tone: str,
) -> None:
    activity = RuntimeActivityTracker().update(
        state,
        source="runtime",
        detail=f"{state} fixture",
        last_event=f"{state}_event",
        last_error="fixture error" if state == "error" else None,
    )

    view = build_presence_window_view(activity)

    assert view.state == state
    assert view.mode == expected_mode
    assert view.visible is expected_visible
    assert view.tone == expected_tone
    assert view.width == 392
    assert view.min_height == 112


def test_presence_window_view_redacts_and_truncates_sensitive_detail() -> None:
    long_secret = (
        "Please use api_key=sk-live-very-secret-token-value and then continue "
        "with a very long sentence that should not be allowed to resize the "
        "native status window beyond its stable bounds."
    )
    activity = RuntimeActivityTracker().update(
        "error",
        source="dictation",
        detail="ignored when last_error exists",
        last_error=long_secret,
    )

    view = build_presence_window_view(activity)

    assert view.tone == "error"
    assert view.label == "Needs attention"
    assert "sk-live-very-secret-token-value" not in view.detail
    assert "api_key=[redacted]" in view.detail
    assert len(view.detail) <= view.max_detail_chars + 1
