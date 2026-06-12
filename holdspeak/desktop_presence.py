"""Desktop presence host + renderer seam for transient activity surfaces.

Phase 41. The web presence card (HS-41-02) shows runtime activity in the
dashboard; this module is the **desktop** side — an opt-in
(`HOLDSPEAK_DESKTOP_PRESENCE=1`), per-platform native surface so a user dictating
into another app still knows what the copilot is doing.

It is a *seam*, not a renderer: the `PresenceRenderer` Protocol abstracts the
platform surface (macOS `NSStatusItem` + `NSPanel` webview in HS-41-04; Linux
notification + tray in HS-41-05), `DesktopPresenceHost` applies the transient
show/linger/hide window policy, and `build_desktop_presence_host()` probes the
environment and selects the best available renderer (or None). With no native
renderer available — or the flag unset — it returns None and nothing renders.

`build_presence_window_view()` is the renderer-ready, secret-redacted projection
of one activity snapshot; native renderers that can't use the web design system
(a tray glyph color, a notification icon) read its `tone`/`accent` from here.
The codex spike's Tk renderer is deliberately **not** here — see the phase
status doc for why.
"""
from __future__ import annotations

import os
import re
import sys
import threading
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol

from .logging_config import get_logger
from .runtime_activity import desktop_window_policy, normalize_activity_state

log = get_logger("desktop_presence")

_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|access[_-]?token|auth[_-]?token|password)\b\s*[:=]\s*\S+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{12,}")
_OPENAI_KEY_RE = re.compile(r"(?i)\bsk-[a-z0-9-]{12,}")

# Per-state presentation for renderers that can't use the web design tokens
# (the tray glyph / notification icon color). The accent values mirror the
# Signal palette; the web HUD uses the real CSS tokens instead.
_STATE_META: dict[str, dict[str, str]] = {
    "idle": {"tone": "neutral", "label": "Ready", "accent": "#8b95a7"},
    "listening": {"tone": "recording", "label": "Listening", "accent": "#ff6b35"},
    "recording": {"tone": "recording", "label": "Recording", "accent": "#ff6b35"},
    "transcribing": {"tone": "working", "label": "Transcribing", "accent": "#5aa7ff"},
    "processing": {"tone": "working", "label": "Processing", "accent": "#7bd88f"},
    "typing": {"tone": "working", "label": "Typing", "accent": "#d6a4ff"},
    "complete": {"tone": "complete", "label": "Complete", "accent": "#7bd88f"},
    "meeting_live": {"tone": "recording", "label": "Meeting live", "accent": "#ff6b35"},
    "saving": {"tone": "working", "label": "Saving", "accent": "#f6c356"},
    "error": {"tone": "error", "label": "Needs attention", "accent": "#ff5a67"},
    # HS-60: the wake word's bounded armed window — amber, unmistakably hot.
    "armed": {"tone": "recording", "label": "Armed", "accent": "#f6c356"},
}


@dataclass(frozen=True)
class PresenceWindowView:
    """Renderer-ready, secret-safe projection of one activity snapshot."""

    state: str
    tone: str
    label: str
    detail: str
    event: str
    accent: str
    visible: bool
    mode: str
    width: int = 392
    min_height: int = 112
    max_detail_chars: int = 156


# HS-56-05: the native HUD's two frames. Passive (ring/dock only) keeps the
# exact Phase-41 geometry and stays click-through; a presented Qlippy card
# sizes the panel up and accepts pointer events — while the panel itself stays
# non-activating, so keyboard focus never leaves the user's app. The card's
# presence is read from the page itself (`#qlippy-card.is-in`): the activity
# payload cannot know about cards (they ride other broadcasts), so the page —
# which owns the card lifecycle — is the one honest source.
PANEL_FRAME_PASSIVE: dict[str, object] = {"width": 408, "height": 132, "interactive": False}
PANEL_FRAME_CARD: dict[str, object] = {"width": 408, "height": 460, "interactive": True}

#: The probe native webviews evaluate to learn whether a card is showing.
#: Matches the HS-56-02 shell's contract: the card element slides in with
#: `is-in`. With the mascot off the element never gains the class, so the
#: panel never leaves the passive frame.
PANEL_CARD_PROBE_JS = (
    "(function(){var c=document.getElementById('qlippy-card');"
    "return !!(c && c.classList.contains('is-in'));})()"
)


def presence_panel_frame(card_visible: bool) -> dict[str, object]:
    """The native panel frame for the current card state (pure, testable).

    Returns a fresh dict (renderers may annotate it) with ``width``,
    ``height``, and ``interactive`` — interactive meaning the panel should
    accept pointer events; it must never mean "may take keyboard focus".
    """
    return dict(PANEL_FRAME_CARD if card_visible else PANEL_FRAME_PASSIVE)


def _truncate(value: object, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)].rstrip() + "…"


def _redact_sensitive(value: object) -> str:
    text = str(value or "")
    text = _SECRET_VALUE_RE.sub(r"\1=[redacted]", text)
    text = _BEARER_RE.sub("Bearer [redacted]", text)
    text = _OPENAI_KEY_RE.sub("sk-[redacted]", text)
    return text


def build_presence_window_view(activity: dict[str, object]) -> PresenceWindowView:
    """Normalize one runtime activity payload into renderer-safe UI data."""
    state = normalize_activity_state(activity.get("state"))
    meta = _STATE_META.get(state, _STATE_META["idle"])
    window = activity.get("window")
    policy = window if isinstance(window, dict) else desktop_window_policy(state)
    mode = str(policy.get("mode") or "hidden")
    visible = bool(policy.get("visible"))
    raw_detail = (
        activity.get("last_error")
        if state == "error" and activity.get("last_error")
        else activity.get("detail")
    )
    detail = _truncate(_redact_sensitive(raw_detail), 156)
    event = _truncate(activity.get("last_event"), 72)
    return PresenceWindowView(
        state=state,
        tone=meta["tone"],
        label=_truncate(activity.get("label") or meta["label"], 42),
        detail=detail,
        event=event,
        accent=meta["accent"],
        visible=visible,
        mode=mode,
    )


class PresenceRenderer(Protocol):
    """Renderer interface for the desktop presence surface."""

    def show(self, activity: dict[str, object]) -> None: ...

    def update(self, activity: dict[str, object]) -> None: ...

    def hide(self, *, reason: str = "") -> None: ...

    def close(self) -> None: ...


class NullPresenceRenderer:
    """No-op renderer used when desktop presence is disabled/unavailable."""

    def show(self, activity: dict[str, object]) -> None:
        _ = activity

    def update(self, activity: dict[str, object]) -> None:
        _ = activity

    def hide(self, *, reason: str = "") -> None:
        _ = reason

    def close(self) -> None:
        return None


TimerFactory = Callable[[float, Callable[[], None]], Any]


def _default_timer_factory(delay_seconds: float, callback: Callable[[], None]) -> threading.Timer:
    timer = threading.Timer(delay_seconds, callback)
    timer.daemon = True
    timer.start()
    return timer


class DesktopPresenceHost:
    """Applies the transient desktop-window policy to runtime activity events.

    Idle never shows; active work shows immediately and updates in place;
    terminal states linger briefly then hide. A new event cancels a pending
    linger so the surface tracks the live state.
    """

    def __init__(
        self,
        renderer: PresenceRenderer,
        *,
        timer_factory: TimerFactory = _default_timer_factory,
    ) -> None:
        self.renderer = renderer
        self._timer_factory = timer_factory
        self._hide_timer: Any = None
        self._visible = False
        self._lock = threading.Lock()

    @property
    def visible(self) -> bool:
        with self._lock:
            return self._visible

    def handle_activity(self, activity: dict[str, object]) -> None:
        window = activity.get("window")
        policy = window if isinstance(window, dict) else desktop_window_policy(activity.get("state"))
        mode = str(policy.get("mode") or "hidden")
        visible = bool(policy.get("visible"))
        linger_ms = int(policy.get("linger_ms") or 0)

        with self._lock:
            self._cancel_hide_timer_locked()
            if not visible or mode == "hidden":
                self.renderer.hide(reason=mode)
                self._visible = False
                return

            if self._visible:
                self.renderer.update(activity)
            else:
                self.renderer.show(activity)
                self._visible = True

            if mode == "linger" and linger_ms > 0:
                self._hide_timer = self._timer_factory(
                    linger_ms / 1000.0,
                    self._hide_after_linger,
                )

    def close(self) -> None:
        with self._lock:
            self._cancel_hide_timer_locked()
            self._visible = False
        self.renderer.close()

    def _hide_after_linger(self) -> None:
        with self._lock:
            self.renderer.hide(reason="linger_elapsed")
            self._visible = False
            self._hide_timer = None

    def _cancel_hide_timer_locked(self) -> None:
        timer = self._hide_timer
        self._hide_timer = None
        if timer is not None and hasattr(timer, "cancel"):
            try:
                timer.cancel()
            except Exception:
                pass


def desktop_presence_enabled(
    env: Optional[dict[str, str]] = None, *, config_enabled: bool = False
) -> bool:
    """True when desktop presence should run.

    HS-43-04: presence is **config-backed** (``config.presence.enabled``, passed
    here as ``config_enabled``). The legacy ``HOLDSPEAK_DESKTOP_PRESENCE`` env var
    is retained as a power-user / headless **override** (force-on), so either path
    enables it.
    """
    if config_enabled:
        return True
    values = os.environ if env is None else env
    raw = str(values.get("HOLDSPEAK_DESKTOP_PRESENCE", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


# Wayland compositors that implement wlr-layer-shell (so a free-floating overlay
# is possible). GNOME/KDE deliberately do not — there the native path is the
# tray glyph + notification (Tier 1), not an overlay.
_WLROOTS_COMPOSITORS = frozenset({"sway", "hyprland", "river", "wayfire", "labwc", "wlroots"})


def _detect_linux_compositor(values: dict[str, str]) -> str:
    if values.get("SWAYSOCK"):
        return "sway"
    if values.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    desktop = " ".join(
        str(values.get(key, "")).lower()
        for key in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
    )
    for name in _WLROOTS_COMPOSITORS:
        if name in desktop:
            return name
    if "gnome" in desktop:
        return "gnome"
    if "kde" in desktop or "plasma" in desktop:
        return "kde"
    return "other"


def detect_presence_platform(
    env: Optional[dict[str, str]] = None, *, platform_name: Optional[str] = None
) -> dict[str, object]:
    """Probe the OS + (on Linux) display server / compositor for the presence tier.

    Returns ``{os, wayland, compositor, overlay_capable}``. ``overlay_capable``
    is True where a free-floating HUD is possible (macOS, Linux/X11, and wlroots
    Wayland); False on mainstream Wayland (GNOME/KDE), where Tier-1 tray +
    notification is the native path.
    """
    values = os.environ if env is None else env
    plat = platform_name if platform_name is not None else sys.platform
    if plat == "darwin":
        return {"os": "macos", "wayland": False, "compositor": None, "overlay_capable": True}
    if plat.startswith("linux"):
        wayland = bool(str(values.get("WAYLAND_DISPLAY", "")).strip())
        compositor = _detect_linux_compositor(values) if wayland else "x11"
        overlay_capable = (not wayland) or compositor in _WLROOTS_COMPOSITORS
        return {
            "os": "linux",
            "wayland": wayland,
            "compositor": compositor,
            "overlay_capable": overlay_capable,
        }
    return {"os": "other", "wayland": False, "compositor": None, "overlay_capable": False}


def _select_presence_renderer(
    platform: dict[str, object],
    url_provider: Optional[Callable[[], str]],
) -> Optional[PresenceRenderer]:
    """Pick the best available native renderer for the platform, or None.

    macOS (HS-41-04): a non-activating ``NSPanel`` hosting a ``WKWebView`` of the
    ``/presence`` HUD + an ``NSStatusItem`` glyph, when PyObjC/WebKit + a runtime
    URL are available. Linux (HS-41-05) lands next. None on every other case, so
    `build_desktop_presence_host` degrades to None and the web card remains the
    active surface.
    """
    if platform.get("os") == "macos" and url_provider is not None:
        from .desktop_presence_cocoa import CocoaPresenceRenderer, cocoa_presence_available

        if cocoa_presence_available():
            return CocoaPresenceRenderer(url_provider)
    if platform.get("os") == "linux" and url_provider is not None:
        from .desktop_presence_freedesktop import (
            FreedesktopPresenceRenderer,
            freedesktop_presence_available,
        )

        if freedesktop_presence_available():
            return FreedesktopPresenceRenderer(
                url_provider, overlay_capable=bool(platform.get("overlay_capable"))
            )
    return None


def build_desktop_presence_host(
    env: Optional[dict[str, str]] = None,
    *,
    url_provider: Optional[Callable[[], str]] = None,
    config_enabled: bool = False,
) -> Optional[DesktopPresenceHost]:
    """Build the opt-in desktop host, or None (off / no native renderer).

    Enabled by ``config.presence.enabled`` (passed as ``config_enabled``, HS-43-04)
    or the legacy ``HOLDSPEAK_DESKTOP_PRESENCE`` env override. `url_provider` is a
    lazy callable returning the runtime base URL; the macOS renderer reads it at
    first show to load ``/presence``. Defensive: a renderer that fails to construct
    never stops the runtime — it falls back to None and the web card stays active.
    """
    if not desktop_presence_enabled(env, config_enabled=config_enabled):
        return None
    platform = detect_presence_platform(env)
    try:
        renderer = _select_presence_renderer(platform, url_provider)
    except Exception as exc:  # pragma: no cover - presence must never block boot
        log.warning(f"Desktop presence renderer unavailable: {exc}")
        return None
    if renderer is None:
        log.info(
            "Desktop presence enabled but no native renderer is available on "
            f"this platform yet ({platform.get('os')}); using the web card only."
        )
        return None
    return DesktopPresenceHost(renderer)


__all__ = [
    "DesktopPresenceHost",
    "NullPresenceRenderer",
    "PANEL_CARD_PROBE_JS",
    "PANEL_FRAME_CARD",
    "PANEL_FRAME_PASSIVE",
    "PresenceRenderer",
    "PresenceWindowView",
    "build_desktop_presence_host",
    "build_presence_window_view",
    "desktop_presence_enabled",
    "detect_presence_platform",
    "presence_panel_frame",
]
