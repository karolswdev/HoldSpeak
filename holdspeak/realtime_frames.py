"""The one realtime frame vocabulary (HS-132-03).

Every live WebSocket frame the hub broadcasts, and every frame the web
consumes, is named exactly once — here. The registry is not decoration:
``tests/test_realtime_frame_registry.py`` re-derives the emitter and consumer
sets from the two trees and refuses any frame type that is only half wired
(emitted to nobody, or listened for by nobody).

Article XI.5 binds ``intel_token``: a token stream is display material only.
It is broadcast so a live surface can show intelligence arriving; it is never
journaled, never persisted, never replayed.

## The recognized idioms

The scanners below read source, not runtime, so they only see the shapes the
codebase actually uses. Any new emitter or consumer MUST use one of them, or
the guard will report it as one-sided:

Python emitters (``holdspeak/``)
  ``<anything>broadcast("frame_type", payload)`` — covers ``ctx.broadcast``,
  ``self.server.broadcast``, ``self._emit_broadcast``, the bare ``broadcast``
  callback, and the workbench conductor's ``_emit_broadcast``.
  ``BroadcastMessage(type="frame_type", ...)`` — the web server's direct sends.

Web consumers (``web/src/``, tests excluded — a test is not a consumer)
  ``subscribe("frame_type", ...)``
  ``useRuntimeFrame<T>("frame_type")``
  ``frame.type === "frame_type"``
  ``["a", "b"].includes(frame.type)``
"""

from __future__ import annotations

import re
from pathlib import Path

# --------------------------------------------------------------- vocabulary

#: Every live frame type the desk speaks. Sorted; one line each, with the
#: surface that hears it, so a reader can trace a frame end to end.
RUNTIME_FRAME_TYPES: tuple[str, ...] = (
    "actuator_proposed",        # a proposal awaits a decision
    "actuator_result",          # a proposal was decided/executed
    "aftercare_ready",          # a finished meeting has aftercare
    "audio_level",              # live mic level
    "bookmark",                 # a moment was named mid-meeting
    "capture_recovery",         # capture degraded and wants a choice
    "device_health",            # an attached device's battery/RSSI moved
    "dictation_preview",        # dictation is held for preview
    "duration",                 # the live meeting clock
    "intel_complete",           # a meeting intelligence window landed
    "intel_status",             # any run's running/ready/error state
    "intel_token",              # Article XI.5: display only, never journaled
    "intent_controls_updated",  # the intent routing dial moved
    "learning_event",           # the pipeline learned something
    "meeting_started",          # a meeting began
    "meeting_updated",          # title/tags changed mid-meeting
    "plugin_jobs_processed",    # the deferred plugin queue was drained
    "runtime_activity",         # the one activity line
    "runtime_queue",            # the deferred intel queue's real truth
    "scheduled_recording.arming",    # countdown before a scheduled capture fires
    "scheduled_recording.cancelled", # a scheduled capture was cancelled mid-countdown
    "scheduled_recording.missed",    # a scheduled capture's fire time was missed
    "scheduled_recording.refused",   # a scheduled capture was refused (mic floor held)
    "scheduled_recording.started",   # a scheduled capture started recording
    "scheduled_recording.stopped",   # a scheduled capture stopped (auto-stop or manual)
    "segment",                  # one finalized transcript segment
    "stopped",                  # the meeting stopped
    "wake_armed",               # the wake word armed its capture window
    "wake_preview",             # a wake capture is held for preview
    "workbench.item_claimed",   # a run took an item
    "workbench.item_done",      # an item produced output
    "workbench.item_failed",    # an item failed
    "workbench.run_complete",   # the run reached its terminal
    "workbench.run_start",      # a workbench run began
)

#: Frames the hub emits that no web surface listens for, WITH the reason.
#: Every entry here is a deliberate, named exception — never a silent one.
EMITTED_WITHOUT_CONSUMER: dict[str, str] = {
    "wake_armed": (
        "Dormant desktop wake-word leg: arming is a host-side hotkey window "
        "with no web affordance; the web consumes only its result "
        "(wake_preview)."
    ),
}

#: Frames the web listens for that the hub never emits, WITH the reason.
#: Empty is the correct state: a subscription with no emitter is dead code.
CONSUMED_WITHOUT_EMITTER: dict[str, str] = {}

#: The generated/mirrored web copy of :data:`RUNTIME_FRAME_TYPES`.
WEB_MIRROR_PATH = "web/src/runtime/frames.ts"


def repo_root() -> Path:
    """The repository root (this file lives at ``<root>/holdspeak/``)."""
    return Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------ scanners

_EMIT_PATTERNS = (
    re.compile(r'broadcast\(\s*"([a-z_][a-z0-9_.]*)"'),
    re.compile(r'BroadcastMessage\(\s*type\s*=\s*"([a-z_][a-z0-9_.]*)"'),
)

_CONSUME_PATTERNS = (
    re.compile(r'subscribe\(\s*"([a-z_][a-z0-9_.]*)"'),
    re.compile(r'useRuntimeFrame(?:<[^>]*>)?\(\s*"([a-z_][a-z0-9_.]*)"'),
    re.compile(r'frame\.type\s*===\s*"([a-z_][a-z0-9_.]*)"'),
    re.compile(r'"([a-z_][a-z0-9_.]*)"\s*===\s*frame\.type'),
)

_INCLUDES_FRAME_TYPE = re.compile(
    r"\[([^\]]*)\]\s*\.includes\(\s*frame\.type", re.S
)
_QUOTED = re.compile(r'"([a-z_][a-z0-9_.]*)"')


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan_emitters(root: Path | None = None) -> dict[str, list[str]]:
    """Frame type -> ``path:line`` for every broadcast in ``holdspeak/``."""
    base = (root or repo_root()) / "holdspeak"
    found: dict[str, list[str]] = {}
    for path in sorted(base.rglob("*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue  # the registry documents the idioms; it emits nothing
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in _EMIT_PATTERNS:
            for match in pattern.finditer(text):
                site = f"{path.relative_to(root or repo_root())}:{_line_of(text, match.start())}"
                found.setdefault(match.group(1), []).append(site)
    return found


def scan_consumers(root: Path | None = None) -> dict[str, list[str]]:
    """Frame type -> ``path:line`` for every live consumer in ``web/src/``."""
    repo = root or repo_root()
    base = repo / "web" / "src"
    mirror = (repo / WEB_MIRROR_PATH).resolve()
    found: dict[str, list[str]] = {}
    for path in sorted([*base.rglob("*.ts"), *base.rglob("*.tsx")]):
        if path.resolve() == mirror:
            continue  # the registry mirror names every frame; it consumes none
        if ".test." in path.name or "__tests__" in path.parts:
            continue  # a test that fabricates a frame is not a consumer
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(repo)
        for pattern in _CONSUME_PATTERNS:
            for match in pattern.finditer(text):
                found.setdefault(match.group(1), []).append(
                    f"{rel}:{_line_of(text, match.start())}"
                )
        for match in _INCLUDES_FRAME_TYPE.finditer(text):
            line = _line_of(text, match.start())
            for name in _QUOTED.findall(match.group(1)):
                found.setdefault(name, []).append(f"{rel}:{line}")
    return found


def read_web_mirror(root: Path | None = None) -> tuple[str, ...]:
    """The frame names declared by the web mirror, in file order."""
    path = (root or repo_root()) / WEB_MIRROR_PATH
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"RUNTIME_FRAME_TYPES\s*=\s*\[(.*?)\]\s*as\s+const", text, re.S
    )
    if match is None:
        raise AssertionError(f"{WEB_MIRROR_PATH} has no RUNTIME_FRAME_TYPES array")
    return tuple(_QUOTED.findall(match.group(1)))
