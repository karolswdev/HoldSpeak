"""macOS native presence renderer (HS-41-04).

Renders the runtime-presence surface natively on macOS:

- a **non-activating** ``NSPanel`` (``NSWindowStyleMaskNonactivatingPanel``,
  floating level, shadowed, click-through) that hosts a ``WKWebView`` loaded at
  the local ``/presence`` URL — so the HUD *is* the Signal web card, with zero
  redesign and live updates over the same websocket; and
- an ``NSStatusItem`` menu-bar glyph in the accent color keyed to state.

The non-activating panel is the **focus-safe** choice: showing it never makes
HoldSpeak the active app, so the keystrokes the dictation pipeline injects keep
landing in the frontmost app. AppKit owns a runloop, so the UI runs in a child
process driven over a command queue (the parent runtime stays untouched). When
PyObjC/WebKit is unavailable the renderer is simply not selected and the web
card stays the surface.
"""
from __future__ import annotations

import multiprocessing
import queue
import threading
from typing import Any, Callable

from .desktop_presence import (
    PANEL_CARD_PROBE_JS,
    PANEL_FRAME_PASSIVE,
    presence_panel_frame,
)
from .logging_config import get_logger

log = get_logger("desktop_presence_cocoa")

PRESENCE_STATUS_PROBE_JS = (
    "(function(){var e=document.querySelector('.presence-activity .gadget-lamp');"
    "if(!e)return null;return {available:e.getAttribute('data-on') === 'true'};})()"
)


def _build_status_menu(AppKit: Any, events: Any) -> tuple[Any, Any, Any, Any]:
    """Build the status menu with a real Objective-C Stop action target."""
    import objc
    from Foundation import NSObject

    class _CocoaStopTarget(NSObject):
        def initWithEvents_(self, event_queue: Any):
            self = objc.super(_CocoaStopTarget, self).init()
            if self is not None:
                self._events = event_queue
            return self

        def stop_(self, _sender: Any) -> None:
            try:
                self._events.put(("stop", None))
            except Exception as exc:  # pragma: no cover - AppKit shutdown race
                log.debug("Cocoa Stop event failed: %s", exc)

    menu = AppKit.NSMenu.alloc().init()
    menu.setAutoenablesItems_(False)
    state_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Ready", None, ""
    )
    state_item.setEnabled_(False)
    menu.addItem_(state_item)
    menu.addItem_(AppKit.NSMenuItem.separatorItem())
    stop_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Stop", "stop:", ""
    )
    stop_target = _CocoaStopTarget.alloc().initWithEvents_(events)
    stop_item.setTarget_(stop_target)
    stop_item.setEnabled_(False)
    menu.addItem_(stop_item)
    return menu, state_item, stop_item, stop_target


def cocoa_presence_available() -> bool:
    """True when the macOS native renderer's deps (AppKit + WebKit) import."""
    try:
        import AppKit  # noqa: F401
        import WebKit  # noqa: F401
        import Foundation  # noqa: F401
    except Exception:
        return False
    return True


# ── The AppKit UI (runs in the child process' main thread) ─────────────


class _CocoaPresenceUI:
    """Owns the NSPanel + WKWebView + NSStatusItem. Main-thread only."""

    # The passive (ring/dock-only) geometry — the exact Phase-41 frame. The
    # card frame comes from the same `presence_panel_frame` policy (HS-56-05).
    WIDTH = int(PANEL_FRAME_PASSIVE["width"])
    HEIGHT = int(PANEL_FRAME_PASSIVE["height"])

    def __init__(self, url: str, events: Any = None) -> None:
        import AppKit
        import WebKit
        from Foundation import NSMakeRect, NSURL, NSURLRequest

        self._AppKit = AppKit
        self.app = AppKit.NSApplication.sharedApplication()
        self.app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        # The status-bar glyph (always present while the host is alive).
        self.status_item = AppKit.NSStatusBar.systemStatusBar().statusItemWithLength_(
            AppKit.NSVariableStatusItemLength
        )
        self._events = events
        self._activity: dict[str, Any] = {}
        self._desk_available = True
        self._last_status_signature: tuple[str, bool, str] | None = None
        (
            self.status_menu,
            self.status_state_item,
            self.stop_menu_item,
            self._stop_target,
        ) = _build_status_menu(AppKit, events)
        self.status_item.setMenu_(self.status_menu)
        self._set_glyph("#8b95a7")

        # A non-activating, borderless, floating, click-through panel.
        style = (
            AppKit.NSWindowStyleMaskBorderless
            | AppKit.NSWindowStyleMaskNonactivatingPanel
        )
        rect = NSMakeRect(0, 0, self.WIDTH, self.HEIGHT)
        self.panel = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, AppKit.NSBackingStoreBuffered, False
        )
        self.panel.setLevel_(AppKit.NSStatusWindowLevel)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.panel.setHasShadow_(True)
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorStationary
            | AppKit.NSWindowCollectionBehaviorIgnoresCycle
        )

        config = WebKit.WKWebViewConfiguration.alloc().init()
        self.webview = WebKit.WKWebView.alloc().initWithFrame_configuration_(rect, config)
        # Transparent webview so the page's own rounded card + shadow show.
        try:
            self.webview.setValue_forKey_(False, "drawsBackground")
        except Exception:
            pass
        try:
            self.webview.setUnderPageBackgroundColor_(AppKit.NSColor.clearColor())
        except Exception:
            pass
        # The webview follows the panel through the HS-56-05 card resize.
        self.webview.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
        )
        self.panel.setContentView_(self.webview)
        self.webview.loadRequest_(
            NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        )
        # HS-56-05 card-frame state: what the panel currently shows, and the
        # latest probe answer from the page (applied on the next pump tick).
        self._width = self.WIDTH
        self._height = self.HEIGHT
        self._card_visible = False
        self._card_seen = False
        self._panel_shown = False  # the activity policy's say (show/hide)
        self._position()

    def _position(self) -> None:
        AppKit = self._AppKit
        screen = AppKit.NSScreen.mainScreen()
        if screen is None:
            return
        frame = screen.visibleFrame()
        x = frame.origin.x + frame.size.width - self._width - 22
        # Cocoa origins are bottom-left; subtracting the current height keeps
        # the panel's TOP edge fixed, so a card grows the frame downward.
        y = frame.origin.y + frame.size.height - self._height - 14
        self.panel.setFrameOrigin_((x, y))

    # ── HS-56-05: the card frame ────────────────────────────────────────

    def poll_card(self) -> None:
        """Ask the page whether a Qlippy card is showing (async, main-thread)."""

        def _done(result: Any, _error: Any) -> None:
            self._card_seen = bool(result)

        try:
            self.webview.evaluateJavaScript_completionHandler_(PANEL_CARD_PROBE_JS, _done)
        except Exception:  # pragma: no cover - GUI session dependent
            pass

    def poll_status(self) -> None:
        """Read the existing presence page's connection lamp.

        The native child has no second hub connection. The page's RuntimeBus is
        the established connection truth, so a false lamp changes only the
        native status label and disables Stop until the desk reconnects.
        """

        def _done(result: Any, _error: Any) -> None:
            if not isinstance(result, dict) or not isinstance(result.get("available"), bool):
                return
            self._desk_available = bool(result["available"])
            self.refresh_status()

        try:
            self.webview.evaluateJavaScript_completionHandler_(PRESENCE_STATUS_PROBE_JS, _done)
        except Exception:  # pragma: no cover - GUI session dependent
            pass

    def sync_card_frame(self) -> None:
        """Apply the latest probe answer when it differs from the panel."""
        if self._card_seen != self._card_visible:
            self.apply_card_frame(self._card_seen)

    def apply_card_frame(self, card_visible: bool) -> None:
        """Resize the panel per the frame policy + manage pointer events.

        A presented card needs clickable buttons, so `ignoresMouseEvents`
        turns off — but ONLY then, and the non-activating style mask is
        untouched, so the panel never takes keyboard focus either way.
        Passive states return to the exact Phase-41 click-through frame.
        """
        from Foundation import NSMakeRect

        spec = presence_panel_frame(card_visible)
        self._width = int(spec["width"])
        self._height = int(spec["height"])
        self._card_visible = bool(card_visible)
        AppKit = self._AppKit
        screen = AppKit.NSScreen.mainScreen()
        if screen is not None:
            frame = screen.visibleFrame()
            x = frame.origin.x + frame.size.width - self._width - 22
            y = frame.origin.y + frame.size.height - self._height - 14
            self.panel.setFrame_display_(
                NSMakeRect(x, y, self._width, self._height), True
            )
        self.panel.setIgnoresMouseEvents_(not bool(spec["interactive"]))
        if self._card_visible:
            # A card needs to be seen even when the activity policy has the
            # panel hidden (e.g. a proposal arrives while idle).
            self.panel.orderFrontRegardless()
        elif not self._panel_shown:
            # The card resolved and the activity policy wants the panel gone.
            self.panel.orderOut_(None)
            self._set_glyph("#8b95a7")

    def _set_glyph(self, accent_hex: str) -> None:
        AppKit = self._AppKit
        size = 16.0
        image = AppKit.NSImage.alloc().initWithSize_((size, size))
        image.lockFocus()
        inset = AppKit.NSMakeRect(2.5, 2.5, size - 5, size - 5)
        # A contrasting halo so the state-colored dot reads on a light, dark, or
        # wallpaper-tinted menu bar; then the accent fill conveys the state.
        AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(1, 1, 1, 0.55).setStroke()
        halo = AppKit.NSBezierPath.bezierPathWithOvalInRect_(inset)
        halo.setLineWidth_(2.4)
        halo.stroke()
        _ns_color(AppKit, accent_hex).setFill()
        AppKit.NSBezierPath.bezierPathWithOvalInRect_(inset).fill()
        image.unlockFocus()
        image.setTemplate_(False)
        button = self.status_item.button()
        if button is not None:
            button.setImage_(image)

    def _activity_for_view(self) -> dict[str, Any]:
        activity = dict(self._activity)
        activity["desk_available"] = self._desk_available
        return activity

    def refresh_status(self) -> None:
        """Refresh the glyph title from the current activity and wall clock."""
        if not self._activity:
            return
        from .desktop_presence import build_presence_window_view

        view = build_presence_window_view(self._activity_for_view())
        signature = (view.label, view.stop_available, view.accent)
        if signature == self._last_status_signature:
            return
        self._last_status_signature = signature
        self._set_glyph(view.accent)
        self.status_state_item.setTitle_(view.label)
        self.stop_menu_item.setEnabled_(view.stop_available)
        button = self.status_item.button()
        if button is not None:
            button.setToolTip_(view.label)

    def show(self, activity: dict[str, Any]) -> None:
        self._activity = dict(activity)
        self._desk_available = True
        self.refresh_status()
        self._position()
        self.panel.orderFrontRegardless()
        self._panel_shown = True

    def update(self, activity: dict[str, Any]) -> None:
        # The webview self-updates over the websocket; we only refresh the glyph.
        self._activity = dict(activity)
        self.refresh_status()

    def hide(self, *, reason: str = "") -> None:
        self._panel_shown = False
        # A card awaiting the user outlives the activity linger: keep the
        # panel up until the card resolves (ignoring it is always safe — it
        # will drop the panel the moment it goes).
        if self._card_visible:
            return
        self.panel.orderOut_(None)
        keep_live_status = reason == "linger_elapsed" and self._activity.get("state") == "meeting_live"
        if not keep_live_status:
            self._set_glyph("#8b95a7")
            self.status_state_item.setTitle_("Ready")
            self.stop_menu_item.setEnabled_(False)
        self._card_seen = False
        if not keep_live_status:
            self._last_status_signature = None

    def pump(self, seconds: float) -> None:
        from Foundation import NSDate, NSRunLoop

        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(seconds)
        )


def _ns_color(AppKit: Any, hex_str: str):
    h = hex_str.lstrip("#")
    if len(h) != 6:
        h = "8b95a7"
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, 1.0)


# ── The child process entrypoint ──────────────────────────────────────


def _cocoa_notify(payload: dict) -> None:
    """HS-171-05: post a desktop notification via osascript.

    Called inside the AppKit child process.  UNUserNotificationCenter is
    NOT importable (the PyObjC ``UserNotifications`` bridge is missing),
    so the design's osascript fallback is used.
    """
    import subprocess as _sp

    from .desktop_notify import desktop_notify_enabled

    if not desktop_notify_enabled():
        return
    title = str(payload.get("title", "HoldSpeak"))
    body = str(payload.get("body", ""))
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{safe_body}" with title "{safe_title}"'
    try:
        _sp.run(["osascript", "-e", script], timeout=5, capture_output=True, check=False)
    except Exception as exc:
        log.debug("cocoa child osascript notify failed: %s", exc)


def _cocoa_child_main(commands, events, ready, closed, errors, url: str) -> None:
    try:
        ui = _CocoaPresenceUI(url, events)
    except Exception as exc:  # pragma: no cover - GUI session dependent
        errors.put(str(exc))
        ready.set()
        closed.set()
        return

    ready.set()
    running = True
    ticks = 0
    while running:
        # HS-56-05: ~every 0.4 s ask the page whether a Qlippy card is up and
        # apply the frame policy. Cheap (one async JS probe), main-thread.
        ticks += 1
        if ticks % 8 == 0:
            ui.poll_card()
            ui.poll_status()
            ui.sync_card_frame()
        if ticks % 20 == 0:
            ui.refresh_status()
        try:
            command, payload = commands.get_nowait()
        except queue.Empty:
            ui.pump(0.05)
            continue
        try:
            if command == "show" and isinstance(payload, dict):
                ui.show(payload)
            elif command == "update" and isinstance(payload, dict):
                ui.update(payload)
            elif command == "hide":
                ui.hide(reason=str(payload or ""))
            elif command == "notify" and isinstance(payload, dict):
                # HS-171-05: post a desktop notification from the AppKit child.
                # UNUserNotificationCenter is unavailable; use osascript.
                _cocoa_notify(payload)
            elif command == "close":
                ui.hide(reason="close")
                running = False
        except Exception as exc:  # pragma: no cover - GUI session dependent
            log.debug(f"Cocoa presence command {command!r} failed: {exc}")
        ui.pump(0.02)
    closed.set()


# ── The parent-side renderer (PresenceRenderer) ───────────────────────


class CocoaPresenceRenderer:
    """Drives the macOS presence UI in a child process over a command queue.

    The child (which loads the ``/presence`` webview) is spawned **lazily on the
    first ``show``** — by then the runtime server is up and `url_provider`
    resolves a real URL. Construction is cheap, so the host can be wired at
    runtime ``__init__`` before the server has a port.
    """

    def __init__(
        self,
        url_provider: Callable[[], str],
        *,
        stop_callback: Callable[[], Any] | None = None,
        start_timeout: float = 5.0,
    ) -> None:
        self._url_provider = url_provider
        self._stop_callback = stop_callback
        self._start_timeout = start_timeout
        self._commands: Any = None
        self._events: Any = None
        self._closed: Any = None
        self._process: Any = None
        self._started = False
        self._unavailable = False
        self._event_stop = threading.Event()
        self._event_thread: threading.Thread | None = None

    def _consume_events(self) -> None:
        while not self._event_stop.is_set():
            try:
                command, _payload = self._events.get(timeout=0.2)
            except queue.Empty:
                continue
            if command != "stop" or self._stop_callback is None:
                continue
            try:
                self._stop_callback()
            except Exception as exc:  # pragma: no cover - runtime stop boundary
                log.warning("Native Stop failed: %s", exc)

    def _ensure_started(self) -> bool:
        if self._started:
            return True
        if self._unavailable:
            return False
        url = str(self._url_provider() or "").rstrip("/")
        if not url:
            return False  # server not up yet; try again on the next event
        presence_url = f"{url}/presence"

        ctx = multiprocessing.get_context("spawn")
        self._commands = ctx.Queue()
        self._events = ctx.Queue()
        ready = ctx.Event()
        self._closed = ctx.Event()
        errors = ctx.Queue()
        self._process = ctx.Process(
            target=_cocoa_child_main,
            args=(self._commands, self._events, ready, self._closed, errors, presence_url),
            name="HoldSpeakDesktopPresenceCocoa",
            daemon=True,
        )
        self._process.start()
        if not ready.wait(timeout=self._start_timeout):
            self._unavailable = True
            self.close()
            log.warning("macOS presence renderer timed out starting; using the web card.")
            return False
        try:
            err = errors.get_nowait()
        except queue.Empty:
            err = ""
        if err:
            self._unavailable = True
            self.close()
            log.warning(f"macOS presence renderer unavailable ({err}); using the web card.")
            return False
        self._started = True
        if self._stop_callback is not None:
            self._event_stop.clear()
            self._event_thread = threading.Thread(
                target=self._consume_events,
                name="HoldSpeakDesktopPresenceEvents",
                daemon=True,
            )
            self._event_thread.start()
        return True

    def show(self, activity: dict[str, Any]) -> None:
        if self._ensure_started():
            self._commands.put(("show", dict(activity)))

    def update(self, activity: dict[str, Any]) -> None:
        if self._started:
            self._commands.put(("update", dict(activity)))

    def hide(self, *, reason: str = "") -> None:
        if self._started:
            self._commands.put(("hide", str(reason)))

    def close(self) -> None:
        self._event_stop.set()
        if self._commands is not None:
            try:
                self._commands.put(("close", None))
            except Exception:
                pass
        if self._closed is not None:
            self._closed.wait(timeout=2.0)
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=1.0)
        if self._event_thread is not None:
            self._event_thread.join(timeout=1.0)
            self._event_thread = None


__all__ = ["CocoaPresenceRenderer", "cocoa_presence_available"]
