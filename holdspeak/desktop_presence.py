"""Desktop presence host for transient HoldSpeak activity windows."""

from __future__ import annotations

import re
from dataclasses import dataclass
import multiprocessing
import os
import queue
import threading
from typing import Any, Callable, Optional, Protocol

from .logging_config import get_logger
from .runtime_activity import desktop_window_policy

log = get_logger("desktop_presence")

_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|access[_-]?token|auth[_-]?token|password)\b\s*[:=]\s*\S+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{12,}")
_OPENAI_KEY_RE = re.compile(r"(?i)\bsk-[a-z0-9]{12,}")

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
}


@dataclass(frozen=True)
class PresenceWindowView:
    """Renderer-ready shape for the transient desktop window."""

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
    state = str(activity.get("state") or "idle").strip().lower() or "idle"
    meta = _STATE_META.get(state, _STATE_META["idle"])
    window = activity.get("window")
    policy = window if isinstance(window, dict) else desktop_window_policy(state)
    mode = str(policy.get("mode") or "hidden")
    visible = bool(policy.get("visible"))
    raw_detail = activity.get("last_error") if state == "error" and activity.get("last_error") else activity.get("detail")
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
    """Renderer interface for desktop presence windows."""

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


class TkPresenceRenderer:
    """Small optional Tk renderer for transient desktop presence windows.

    Tk ships with many Python desktop installs and gives us a pragmatic first
    native-like window without making GUI dependencies part of the core runtime.
    Tk is run in a child process so macOS can keep Tk on that process' main
    thread; callers only enqueue show/update/hide commands.
    """

    def __init__(self) -> None:
        self._ctx = multiprocessing.get_context("spawn")
        self._commands = self._ctx.Queue()
        self._ready = self._ctx.Event()
        self._closed = self._ctx.Event()
        self._errors = self._ctx.Queue()
        self._process = self._ctx.Process(
            target=_run_tk_renderer_process,
            args=(self._commands, self._ready, self._closed, self._errors),
            name="HoldSpeakDesktopPresenceTk",
            daemon=True,
        )
        self._process.start()
        if not self._ready.wait(timeout=3.0):
            self.close()
            raise RuntimeError("Timed out starting desktop presence renderer")
        try:
            error = self._errors.get_nowait()
        except queue.Empty:
            error = ""
        if error:
            raise RuntimeError(f"Desktop presence renderer unavailable: {error}")

    def show(self, activity: dict[str, object]) -> None:
        self._commands.put(("show", dict(activity)))

    def update(self, activity: dict[str, object]) -> None:
        self._commands.put(("update", dict(activity)))

    def hide(self, *, reason: str = "") -> None:
        self._commands.put(("hide", str(reason)))

    def close(self) -> None:
        self._commands.put(("close", None))
        self._closed.wait(timeout=2.0)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=1.0)


def _run_tk_renderer_process(
    commands: Any,
    ready: Any,
    closed: Any,
    errors: Any,
) -> None:
    try:
        import tkinter as tk
    except Exception as exc:
        errors.put(str(exc))
        ready.set()
        closed.set()
        return

    root = tk.Tk()
    root.title("HoldSpeak")
    root.withdraw()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.focusmodel("passive")
    except Exception:
        pass

    outer = tk.Frame(root, bg="#090b0f", padx=1, pady=1)
    outer.pack(fill="both", expand=True)
    frame = tk.Frame(outer, bg="#111318", padx=14, pady=12)
    frame.pack(fill="both", expand=True)

    top_row = tk.Frame(frame, bg="#111318")
    top_row.pack(fill="x")
    dot = tk.Canvas(
        top_row,
        width=18,
        height=18,
        bg="#111318",
        bd=0,
        highlightthickness=0,
    )
    dot.pack(side="left", padx=(0, 10))
    label_var = tk.StringVar(value="HoldSpeak")
    detail_var = tk.StringVar(value="")
    event_var = tk.StringVar(value="")
    label = tk.Label(
        top_row,
        textvariable=label_var,
        bg="#111318",
        fg="#f5f7fb",
        font=("Helvetica", 15, "bold"),
        anchor="w",
    )
    label.pack(side="left", fill="x", expand=True)
    detail = tk.Label(
        frame,
        textvariable=detail_var,
        bg="#111318",
        fg="#c8ced8",
        font=("Helvetica", 11),
        anchor="w",
        wraplength=320,
        justify="left",
    )
    event = tk.Label(
        frame,
        textvariable=event_var,
        bg="#111318",
        fg="#ff8a4c",
        font=("Menlo", 9),
        anchor="w",
    )
    detail.pack(fill="x", pady=(4, 0))
    event.pack(fill="x", pady=(6, 0))

    def apply_activity(activity: dict[str, object]) -> None:
        view = build_presence_window_view(activity)
        if not view.visible:
            root.withdraw()
            return
        label_var.set(view.label)
        detail_var.set(view.detail)
        event_var.set(view.event)
        dot.delete("all")
        dot.create_oval(3, 3, 15, 15, fill=view.accent, outline=view.accent)
        root.update_idletasks()
        width = view.width
        height = max(view.min_height, root.winfo_reqheight())
        screen_width = root.winfo_screenwidth()
        x = max(24, screen_width - width - 32)
        y = 56
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.deiconify()
        root.lift()

    def pump() -> None:
        while True:
            try:
                command, payload = commands.get_nowait()
            except queue.Empty:
                break
            if command in {"show", "update"} and isinstance(payload, dict):
                apply_activity(payload)
            elif command == "hide":
                root.withdraw()
            elif command == "close":
                root.withdraw()
                root.quit()
                closed.set()
                return
        root.after(50, pump)

    ready.set()
    root.after(50, pump)
    try:
        root.mainloop()
    finally:
        closed.set()


TimerFactory = Callable[[float, Callable[[], None]], Any]


def _default_timer_factory(delay_seconds: float, callback: Callable[[], None]) -> threading.Timer:
    timer = threading.Timer(delay_seconds, callback)
    timer.daemon = True
    timer.start()
    return timer


class DesktopPresenceHost:
    """Applies transient desktop-window policy to runtime activity events."""

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


def desktop_presence_enabled(env: Optional[dict[str, str]] = None) -> bool:
    values = os.environ if env is None else env
    raw = str(values.get("HOLDSPEAK_DESKTOP_PRESENCE", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def build_desktop_presence_host() -> Optional[DesktopPresenceHost]:
    """Build the optional desktop host, returning None on graceful fallback."""
    if not desktop_presence_enabled():
        return None
    try:
        return DesktopPresenceHost(TkPresenceRenderer())
    except Exception as exc:
        log.warning(f"Desktop presence disabled: {exc}")
        return None


__all__ = [
    "DesktopPresenceHost",
    "NullPresenceRenderer",
    "PresenceRenderer",
    "PresenceWindowView",
    "TkPresenceRenderer",
    "build_desktop_presence_host",
    "build_presence_window_view",
    "desktop_presence_enabled",
]
