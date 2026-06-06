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
from typing import Any, Callable

from .logging_config import get_logger

log = get_logger("desktop_presence_cocoa")


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

    WIDTH = 408
    HEIGHT = 132

    def __init__(self, url: str) -> None:
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
        self.panel.setContentView_(self.webview)
        self.webview.loadRequest_(
            NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        )
        self._position()

    def _position(self) -> None:
        AppKit = self._AppKit
        screen = AppKit.NSScreen.mainScreen()
        if screen is None:
            return
        frame = screen.visibleFrame()
        x = frame.origin.x + frame.size.width - self.WIDTH - 22
        y = frame.origin.y + frame.size.height - self.HEIGHT - 14
        self.panel.setFrameOrigin_((x, y))

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

    def show(self, activity: dict[str, Any]) -> None:
        from .desktop_presence import build_presence_window_view

        view = build_presence_window_view(activity)
        self._set_glyph(view.accent)
        self._position()
        self.panel.orderFrontRegardless()

    def update(self, activity: dict[str, Any]) -> None:
        # The webview self-updates over the websocket; we only refresh the glyph.
        from .desktop_presence import build_presence_window_view

        self._set_glyph(build_presence_window_view(activity).accent)

    def hide(self) -> None:
        self.panel.orderOut_(None)
        self._set_glyph("#8b95a7")

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


def _cocoa_child_main(commands, ready, closed, errors, url: str) -> None:
    try:
        ui = _CocoaPresenceUI(url)
    except Exception as exc:  # pragma: no cover - GUI session dependent
        errors.put(str(exc))
        ready.set()
        closed.set()
        return

    ready.set()
    running = True
    while running:
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
                ui.hide()
            elif command == "close":
                ui.hide()
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

    def __init__(self, url_provider: Callable[[], str], *, start_timeout: float = 5.0) -> None:
        self._url_provider = url_provider
        self._start_timeout = start_timeout
        self._commands: Any = None
        self._closed: Any = None
        self._process: Any = None
        self._started = False
        self._unavailable = False

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
        ready = ctx.Event()
        self._closed = ctx.Event()
        errors = ctx.Queue()
        self._process = ctx.Process(
            target=_cocoa_child_main,
            args=(self._commands, ready, self._closed, errors, presence_url),
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


__all__ = ["CocoaPresenceRenderer", "cocoa_presence_available"]
