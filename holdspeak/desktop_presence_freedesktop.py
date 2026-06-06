"""Linux native presence renderer (HS-41-05).

The focus-safe, **everywhere-portable** Linux surface — it works on X11 *and*
Wayland, GNOME/KDE/XFCE alike, because it uses the two freedesktop standards
that every desktop honors and that never steal keyboard focus:

- an **in-place-updating desktop notification** (``org.freedesktop.Notifications``
  via libnotify): one notification that *mutates* as state changes
  (listening → transcribing → typing → done), coalesced so rapid changes don't
  spam, marked ``transient`` so it doesn't pile up in history; and
- a **StatusNotifierItem tray glyph** (AppIndicator) keyed to state — the
  always-visible, branded, ambient layer.

This is Tier 1. A free-floating GTK-WebKit overlay of ``/presence`` (the macOS
HUD's analog) is only possible on X11 + wlroots compositors — *not* on
mainstream Wayland (GNOME/KDE), where the compositor blocks arbitrary overlays —
so it's a separate, overlay-capable-only follow-up; on the dominant desktops the
notification + tray *is* the native experience.

The gi/libnotify/AppIndicator imports are lazy + behind the opt-in flag; when
they're unavailable the renderer degrades to the web card.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Protocol

from .desktop_presence import PresenceWindowView, build_presence_window_view
from .logging_config import get_logger

log = get_logger("desktop_presence_freedesktop")

# freedesktop icon-naming-spec names most themes ship; a missing icon degrades
# to no icon, never an error.
_ICON_BY_STATE = {
    "listening": "audio-input-microphone",
    "recording": "audio-input-microphone",
    "meeting_live": "audio-input-microphone",
    "transcribing": "emblem-synchronizing",
    "processing": "emblem-synchronizing",
    "typing": "input-keyboard",
    "saving": "document-save",
    "complete": "emblem-ok",
    "error": "dialog-error",
    "idle": "audio-input-microphone",
}
# org.freedesktop.Notifications urgency: 0 low, 1 normal, 2 critical.
_URGENCY_BY_STATE = {"idle": 0, "error": 2}


def freedesktop_presence_available() -> bool:
    """True when PyGObject + libnotify (Notify) import (the Tier-1 minimum)."""
    try:
        import gi

        gi.require_version("Notify", "0.7")
        from gi.repository import Notify  # noqa: F401
    except Exception:
        return False
    return True


def notification_for_view(view: PresenceWindowView) -> dict[str, Any]:
    """Pure: project a presence view into notification fields (testable)."""
    return {
        "summary": f"HoldSpeak — {view.label}",
        "body": view.detail,
        "icon": _ICON_BY_STATE.get(view.state, "audio-input-microphone"),
        "urgency": _URGENCY_BY_STATE.get(view.state, 1),
        # Most states are transient (don't persist in history); an error
        # lingers so the user actually sees it.
        "transient": view.state != "error",
    }


class _Notifier(Protocol):
    def notify(self, spec: dict[str, Any]) -> None: ...

    def close(self) -> None: ...


class _Tray(Protocol):
    def set_state(self, view: PresenceWindowView) -> None: ...

    def set_idle(self) -> None: ...

    def close(self) -> None: ...


class _LibnotifyNotifier:
    """Real libnotify notifier — one notification, updated in place."""

    def __init__(self) -> None:
        import gi

        gi.require_version("Notify", "0.7")
        from gi.repository import GLib, Notify

        Notify.init("HoldSpeak")
        self._Notify = Notify
        self._GLib = GLib
        self._notif: Any = None

    def notify(self, spec: dict[str, Any]) -> None:
        if self._notif is None:
            self._notif = self._Notify.Notification.new(
                spec["summary"], spec["body"], spec["icon"]
            )
        else:
            self._notif.update(spec["summary"], spec["body"], spec["icon"])
        try:
            self._notif.set_urgency(spec["urgency"])
            self._notif.set_hint(
                "transient", self._GLib.Variant.new_boolean(bool(spec["transient"]))
            )
        except Exception:
            pass
        self._notif.show()

    def close(self) -> None:
        if self._notif is not None:
            try:
                self._notif.close()
            except Exception:
                pass


class _AppIndicatorTray:
    """Real StatusNotifierItem tray glyph (Ayatana/AppIndicator)."""

    def __init__(self) -> None:
        import gi

        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AI
        except Exception:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3 as AI

        self._AI = AI
        self._ind = AI.Indicator.new(
            "holdspeak-presence",
            "audio-input-microphone",
            AI.IndicatorCategory.APPLICATION_STATUS,
        )
        self._ind.set_status(AI.IndicatorStatus.PASSIVE)

    def set_state(self, view: PresenceWindowView) -> None:
        try:
            self._ind.set_icon_full(_ICON_BY_STATE.get(view.state, "audio-input-microphone"), view.label)
        except Exception:
            pass
        self._ind.set_status(self._AI.IndicatorStatus.ACTIVE)

    def set_idle(self) -> None:
        self._ind.set_status(self._AI.IndicatorStatus.PASSIVE)

    def close(self) -> None:
        self.set_idle()


class FreedesktopPresenceRenderer:
    """Linux presence via notification (in-place) + tray glyph.

    Tier-1, focus-safe, works on every desktop/compositor. Real gi seams are
    built **lazily on first show** (so construction is cheap and injectable for
    tests); `notifier`/`tray` can be injected. The notification is coalesced —
    only re-issued when the activity *state* changes — so a burst of same-state
    updates doesn't spam.
    """

    def __init__(
        self,
        url_provider: Callable[[], str],
        *,
        overlay_capable: bool = False,
        notifier: Optional[_Notifier] = None,
        tray: Optional[_Tray] = None,
        overlay: Optional[Any] = None,
    ) -> None:
        self._url_provider = url_provider
        self._overlay_capable = bool(overlay_capable)
        self._notifier = notifier
        self._tray = tray
        self._overlay = overlay
        self._started = notifier is not None or tray is not None
        self._unavailable = False
        self._last_state: Optional[str] = None

    def _ensure_started(self) -> bool:
        if self._started:
            return True
        if self._unavailable:
            return False
        # The notification is the required core; the tray is best-effort (the
        # AppIndicator typelib is missing on stock GNOME without the extension)
        # — degrade to notification-only rather than fail the whole renderer.
        try:
            if self._notifier is None:
                self._notifier = _LibnotifyNotifier()
        except Exception as exc:  # pragma: no cover - Linux GUI session dependent
            self._unavailable = True
            log.warning(f"Linux presence renderer unavailable ({exc}); using the web card.")
            return False
        if self._tray is None:
            try:
                self._tray = _AppIndicatorTray()
            except Exception as exc:  # pragma: no cover - tray host dependent
                log.info(f"Presence tray unavailable ({exc}); notification-only.")
                self._tray = None
        # Tier-2: a floating GTK-WebKit overlay of /presence, only where the
        # compositor allows it (X11/wlroots) and WebKit2 is present.
        if self._overlay is None and self._overlay_capable:
            try:
                from .desktop_presence_gtk import GtkOverlayRenderer, gtk_overlay_available

                if gtk_overlay_available():
                    self._overlay = GtkOverlayRenderer(self._url_provider)
            except Exception as exc:  # pragma: no cover - Linux GUI dependent
                log.info(f"Presence overlay unavailable ({exc}); notification + tray only.")
                self._overlay = None
        self._started = True
        return True

    def show(self, activity: dict[str, Any]) -> None:
        if not self._ensure_started():
            return
        view = build_presence_window_view(activity)
        if self._tray is not None:
            self._tray.set_state(view)
        if self._overlay is not None:
            self._overlay.show()
        # Coalesce: only (re)notify on a state change, not every event.
        if view.state != self._last_state:
            if self._notifier is not None:
                self._notifier.notify(notification_for_view(view))
            self._last_state = view.state

    def update(self, activity: dict[str, Any]) -> None:
        # Same path; the coalesce guard makes it a no-notify when state is steady.
        self.show(activity)

    def hide(self, *, reason: str = "") -> None:
        if not self._started:
            return
        if self._tray is not None:
            self._tray.set_idle()
        if self._overlay is not None:
            self._overlay.hide()
        if self._notifier is not None:
            self._notifier.close()
        self._last_state = None

    def close(self) -> None:
        if self._notifier is not None:
            self._notifier.close()
        if self._tray is not None:
            self._tray.close()
        if self._overlay is not None:
            self._overlay.close()


__all__ = [
    "FreedesktopPresenceRenderer",
    "freedesktop_presence_available",
    "notification_for_view",
]
