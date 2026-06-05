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

    WIDTH = 408
    HEIGHT = 132

    def __init__(self, url: str) -> None:
        import gi

        gi.require_version("Gtk", "3.0")
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

        # Top-right of the primary monitor.
        display = screen.get_display()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        self._x = geo.x + geo.width - self.WIDTH - 22
        self._y = geo.y + 38

    def show(self) -> None:
        self.win.move(self._x, self._y)
        self.win.show_all()
        gdk_win = self.win.get_window()
        if gdk_win is not None:
            try:
                gdk_win.set_override_redirect(True)
            except Exception:
                pass
        # Click-through: an empty input shape passes all pointer events through.
        try:
            import cairo

            self.win.input_shape_combine_region(cairo.Region())
        except Exception:
            pass

    def hide(self) -> None:
        self.win.hide()

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

    GLib.timeout_add(50, pump)
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

        # fork (the Linux default): the parent never imports gi/GTK, so the
        # child forks clean and initializes GTK fresh. (spawn would force a
        # re-import of the caller's __main__, which breaks stdin-run drivers.)
        ctx = multiprocessing.get_context("fork")
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
