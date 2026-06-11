"""Linux floating GTK-WebKit presence overlay (HS-41-08).

The Tier-2 surface — the macOS HUD's twin on Linux: a frameless, always-on-top,
**non-focus**, click-through GTK3 `POPUP` window hosting a `WebKit2.WebView` of
the local ``/presence`` HUD, so the overlay *is* the Signal web card (same as
macOS). Only possible on **overlay-capable** compositors (X11, wlroots) — on
mainstream Wayland (GNOME/KDE) the compositor blocks arbitrary overlays, so
there the notification + tray (HS-41-05) is the surface.

GTK owns a main loop, so the window runs in a child process driven over a command
queue; the WebView self-updates over the websocket the page connects to. Lazy +
graceful — when gi/Gtk/WebKit2 is unavailable the overlay is simply not used.
"""
from __future__ import annotations

import multiprocessing
import queue
from typing import Any, Callable

from .desktop_presence import (
    PANEL_CARD_PROBE_JS,
    PANEL_FRAME_PASSIVE,
    presence_panel_frame,
)
from .logging_config import get_logger

log = get_logger("desktop_presence_gtk")


def gtk_overlay_available() -> bool:
    """True when GTK3 + a WebKit2 typelib import (the overlay's minimum)."""
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        for ver in ("4.1", "4.0", "6.0"):
            try:
                gi.require_version("WebKit2", ver)
                from gi.repository import WebKit2  # noqa: F401

                return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def _require_webkit2(gi: Any):
    for ver in ("4.1", "4.0", "6.0"):
        try:
            gi.require_version("WebKit2", ver)
            from gi.repository import WebKit2

            return WebKit2
        except Exception:
            continue
    raise RuntimeError("no WebKit2 typelib available")


class _GtkWebKitOverlay:
    """The overlay window. Main-thread (child process) only."""

    # The passive (ring/dock-only) geometry — the exact Phase-41 frame. The
    # card frame comes from the same `presence_panel_frame` policy (HS-56-05).
    WIDTH = int(PANEL_FRAME_PASSIVE["width"])
    HEIGHT = int(PANEL_FRAME_PASSIVE["height"])

    def __init__(self, url: str) -> None:
        import gi

        gi.require_version("Gtk", "3.0")
        # Pin Gdk too: unpinned, gi resolves the NEWEST typelib, so on a box
        # that also ships GTK4 the `Gdk` import grabs 4.0 and then Gtk 3.0's
        # own Gdk-3.0 requirement explodes (found live on real X11 metal,
        # HS-56-05 — present since Phase 41 but latent on GTK3-only boxes).
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, Gtk

        WebKit2 = _require_webkit2(gi)
        self._Gtk = Gtk
        self._Gdk = Gdk

        # POPUP windows are override-redirect (no WM decoration, never focused).
        self.win = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.win.set_decorated(False)
        self.win.set_keep_above(True)
        self.win.set_skip_taskbar_hint(True)
        self.win.set_skip_pager_hint(True)
        self.win.set_accept_focus(False)
        self.win.set_focus_on_map(False)
        self.win.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
        self.win.set_app_paintable(True)
        self.win.set_default_size(self.WIDTH, self.HEIGHT)

        # Transparent window so the page's own rounded card + shadow show.
        screen = self.win.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.win.set_visual(visual)

        self.web = WebKit2.WebView()
        try:
            self.web.set_background_color(Gdk.RGBA(0, 0, 0, 0))
        except Exception:
            pass
        self.web.load_uri(url)
        self.win.add(self.web)

        # Top-right of the primary monitor. GTK origins are top-left, so a
        # taller card frame grows downward with x/y untouched.
        display = screen.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        self._x = geo.x + geo.width - self.WIDTH - 22
        self._y = geo.y + 38

        # HS-56-05 card-frame state (the macOS HUD's analog, best-effort).
        self._card_visible = False
        self._card_seen = False
        self._shown = False

    def show(self) -> None:
        self.win.move(self._x, self._y)
        self.win.show_all()
        self._shown = True
        gdk_win = self.win.get_window()
        if gdk_win is not None:
            try:
                gdk_win.set_override_redirect(True)
            except Exception:
                pass
        self._apply_input_shape()

    def _apply_input_shape(self) -> None:
        """Click-through when passive; pointer events only while a card shows.

        An empty input shape passes every pointer event through. Resetting the
        shape to None restores the full window region so the card's buttons
        click — the window stays `accept_focus(False)`, so keyboard focus
        never moves either way.
        """
        try:
            import cairo

            if self._card_visible:
                self.win.input_shape_combine_region(None)
            else:
                self.win.input_shape_combine_region(cairo.Region())
        except Exception:
            pass

    # ── HS-56-05: the card frame (best-effort; no-hardware posture) ─────

    def poll_card(self) -> None:
        """Ask the page whether a Qlippy card is showing (async)."""

        def _done(web: Any, result: Any) -> None:
            try:
                value = web.run_javascript_finish(result)
                js_value = getattr(value, "get_js_value", lambda: value)()
                self._card_seen = bool(js_value.to_boolean())
            except Exception:
                pass

        try:
            self.web.run_javascript(PANEL_CARD_PROBE_JS, None, _done)
        except Exception:
            pass

    def sync_card_frame(self) -> None:
        if self._card_seen != self._card_visible:
            self.apply_card_frame(self._card_seen)

    def apply_card_frame(self, card_visible: bool) -> None:
        spec = presence_panel_frame(card_visible)
        self._card_visible = bool(card_visible)
        try:
            self.win.resize(int(spec["width"]), int(spec["height"]))
        except Exception:
            pass
        if self._card_visible:
            # A card needs to be seen even while the activity policy has the
            # overlay hidden; `_shown` stays the policy's say.
            self.win.move(self._x, self._y)
            self.win.show_all()
        elif not self._shown:
            # The card resolved and the activity policy wants the overlay gone.
            self.win.hide()
        # After any (re)show: the input shape must match the card state.
        self._apply_input_shape()

    def hide(self) -> None:
        self._shown = False
        # A card awaiting the user outlives the activity linger.
        if self._card_visible:
            return
        self.win.hide()
        self._card_seen = False

    def destroy(self) -> None:
        try:
            self.win.destroy()
        except Exception:
            pass


def _gtk_child_main(commands, ready, closed, errors, url: str) -> None:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import GLib, Gtk

        overlay = _GtkWebKitOverlay(url)
    except Exception as exc:  # pragma: no cover - Linux GUI session dependent
        errors.put(str(exc))
        ready.set()
        closed.set()
        return

    def pump() -> bool:
        try:
            command, _payload = commands.get_nowait()
        except queue.Empty:
            return True
        if command == "show":
            overlay.show()
        elif command == "hide":
            overlay.hide()
        elif command == "close":
            overlay.destroy()
            closed.set()
            Gtk.main_quit()
            return False
        return True

    def poll_card() -> bool:
        # HS-56-05: ~every 0.4 s ask the page whether a Qlippy card is up and
        # apply the frame policy (best-effort; see the module docstring).
        overlay.poll_card()
        overlay.sync_card_frame()
        return True

    GLib.timeout_add(50, pump)
    GLib.timeout_add(400, poll_card)
    ready.set()
    Gtk.main()
    closed.set()


class GtkOverlayRenderer:
    """Parent-side driver for the GTK-WebKit overlay (child process)."""

    def __init__(self, url_provider: Callable[[], str], *, start_timeout: float = 6.0) -> None:
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
            return False
        presence_url = f"{url}/presence"

        # forkserver: by first show the runtime is multi-threaded (uvicorn is
        # up), and fork-from-threads deadlocks the GTK child before it can
        # signal ready (found live on real X11 metal, HS-56-05 — the child
        # timed out every time under a running server, instantly fine without
        # one). forkserver children come from a clean single-threaded server
        # process, and unlike spawn it never re-imports the caller's __main__.
        ctx = multiprocessing.get_context("forkserver")
        self._commands = ctx.Queue()
        ready = ctx.Event()
        self._closed = ctx.Event()
        errors = ctx.Queue()
        self._process = ctx.Process(
            target=_gtk_child_main,
            args=(self._commands, ready, self._closed, errors, presence_url),
            name="HoldSpeakDesktopPresenceGtk",
            daemon=True,
        )
        self._process.start()
        if not ready.wait(timeout=self._start_timeout):
            self._unavailable = True
            self.close()
            log.warning("GTK presence overlay timed out starting; notification-only.")
            return False
        try:
            err = errors.get_nowait()
        except queue.Empty:
            err = ""
        if err:
            self._unavailable = True
            self.close()
            log.info(f"GTK presence overlay unavailable ({err}); notification-only.")
            return False
        self._started = True
        return True

    def show(self) -> None:
        if self._ensure_started():
            self._commands.put(("show", None))

    def hide(self) -> None:
        if self._started:
            self._commands.put(("hide", None))

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


__all__ = ["GtkOverlayRenderer", "gtk_overlay_available"]
