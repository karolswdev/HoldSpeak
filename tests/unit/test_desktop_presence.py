"""HS-41-03: desktop presence host + renderer seam (no native deps)."""

from __future__ import annotations

import pytest

from holdspeak.desktop_presence import (
    DesktopPresenceHost,
    NullPresenceRenderer,
    build_desktop_presence_host,
    build_presence_window_view,
    desktop_presence_enabled,
    detect_presence_platform,
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


# ── Host policy ───────────────────────────────────────────────────────


def test_host_shows_updates_lingers_then_hides() -> None:
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


def test_host_idle_hides_without_linger() -> None:
    renderer = FakeRenderer()
    tracker = RuntimeActivityTracker()
    host = DesktopPresenceHost(renderer, timer_factory=lambda _d, cb: FakeTimer(cb))

    host.handle_activity(tracker.update("recording", source="hotkey"))
    host.handle_activity(tracker.update("idle", source="hotkey"))

    assert renderer.calls == [("show", "recording"), ("hide", "hidden")]
    assert host.visible is False


def test_host_cancels_linger_on_new_activity() -> None:
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
    assert renderer.calls == [
        ("show", "recording"),
        ("update", "complete"),
        ("update", "recording"),
    ]
    assert host.visible is True


def test_host_close_closes_renderer() -> None:
    renderer = FakeRenderer()
    host = DesktopPresenceHost(renderer, timer_factory=lambda _d, cb: FakeTimer(cb))
    host.close()
    assert renderer.calls == [("close", "")]


# ── Enable flag + host builder ────────────────────────────────────────


def test_desktop_presence_enabled_env() -> None:
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "1"}) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "true"}) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "on"}) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "0"}) is False
    assert desktop_presence_enabled({}) is False


def test_build_host_none_when_flag_off() -> None:
    assert build_desktop_presence_host({}) is None


def test_build_host_none_when_no_native_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flag on, but no native renderer is registered yet (HS-41-04/05) → None,
    # so the web card stays the active surface and nothing is half-rendered.
    assert build_desktop_presence_host({"HOLDSPEAK_DESKTOP_PRESENCE": "1"}) is None


def test_build_host_wraps_a_selected_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    # When a renderer *is* available, the builder wraps it in a host.
    renderer = NullPresenceRenderer()
    monkeypatch.setattr(
        "holdspeak.desktop_presence._select_presence_renderer", lambda _p, _u: renderer
    )
    host = build_desktop_presence_host({"HOLDSPEAK_DESKTOP_PRESENCE": "1"})
    assert isinstance(host, DesktopPresenceHost)
    assert host.renderer is renderer


def test_build_host_falls_back_when_renderer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_p, _u):
        raise RuntimeError("no gui")

    monkeypatch.setattr("holdspeak.desktop_presence._select_presence_renderer", boom)
    assert build_desktop_presence_host({"HOLDSPEAK_DESKTOP_PRESENCE": "1"}) is None


def test_select_macos_renderer_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    # macOS + WebKit available + a URL provider → the Cocoa renderer is picked
    # (constructed cheaply; the child process is spawned lazily on first show).
    import holdspeak.desktop_presence as dp

    monkeypatch.setattr("holdspeak.desktop_presence_cocoa.cocoa_presence_available", lambda: True)
    picked = dp._select_presence_renderer({"os": "macos"}, lambda: "http://127.0.0.1:9")
    from holdspeak.desktop_presence_cocoa import CocoaPresenceRenderer

    assert isinstance(picked, CocoaPresenceRenderer)


def test_select_macos_renderer_none_without_webkit(monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.desktop_presence as dp

    monkeypatch.setattr("holdspeak.desktop_presence_cocoa.cocoa_presence_available", lambda: False)
    assert dp._select_presence_renderer({"os": "macos"}, lambda: "http://x") is None


def test_select_renderer_none_without_url_provider() -> None:
    import holdspeak.desktop_presence as dp

    assert dp._select_presence_renderer({"os": "macos"}, None) is None


# ── Platform probe ────────────────────────────────────────────────────


def test_platform_probe_macos() -> None:
    p = detect_presence_platform({}, platform_name="darwin")
    assert p["os"] == "macos"
    assert p["overlay_capable"] is True


def test_platform_probe_linux_x11_is_overlay_capable() -> None:
    p = detect_presence_platform({}, platform_name="linux")
    assert p["os"] == "linux"
    assert p["wayland"] is False
    assert p["compositor"] == "x11"
    assert p["overlay_capable"] is True


def test_platform_probe_wayland_gnome_is_not_overlay_capable() -> None:
    p = detect_presence_platform(
        {"WAYLAND_DISPLAY": "wayland-0", "XDG_CURRENT_DESKTOP": "GNOME"},
        platform_name="linux",
    )
    assert p["wayland"] is True
    assert p["compositor"] == "gnome"
    assert p["overlay_capable"] is False


def test_platform_probe_wayland_sway_is_overlay_capable() -> None:
    p = detect_presence_platform(
        {"WAYLAND_DISPLAY": "wayland-1", "SWAYSOCK": "/run/sway.sock"},
        platform_name="linux",
    )
    assert p["wayland"] is True
    assert p["compositor"] == "sway"
    assert p["overlay_capable"] is True


# ── Renderer-ready view (secret-safe) ─────────────────────────────────


def test_window_view_maps_state_metadata() -> None:
    activity = RuntimeActivityTracker().update(
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
    assert view.accent == "#ff6b35"


def test_window_view_hides_idle() -> None:
    view = build_presence_window_view(RuntimeActivityTracker().snapshot())
    assert view.state == "idle"
    assert view.visible is False
    assert view.mode == "hidden"


def test_window_view_redacts_and_truncates_secret_detail() -> None:
    long_secret = (
        "Please use api_key=sk-live-very-secret-token-value and then continue "
        "with a very long sentence that should not be allowed to resize the "
        "native status window beyond its stable bounds."
    )
    activity = RuntimeActivityTracker().update(
        "error", source="dictation", detail="ignored", last_error=long_secret
    )
    view = build_presence_window_view(activity)
    assert "sk-live-very-secret-token-value" not in view.detail
    assert "api_key=[redacted]" in view.detail
    assert len(view.detail) <= view.max_detail_chars + 1
