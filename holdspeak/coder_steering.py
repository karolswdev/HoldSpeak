"""The desk's window into a live agent session (HS-87-01).

Read side first: `peek_pane` captures a pane's tail through an
injectable runner with a content-hash gate, so a 1-2 s poll from an
open pull-out is cheap enough to be boring (the upstream Telegram
layer's `/live` edit-in-place trick, ported). Typed statuses, never
a 500: a dead pane, a missing tmux, and a record with no pane are
each their own honest state.

The consent spine (arming grants, the delivery chokepoint) lands
here with HS-87-02/03 — watching is free, steering is armed.

Module shape mirrors `missioncontrol_bridge.py`: argv subprocess
via an injectable ``runner``, explicit timeout, `shutil.which`
guard, statuses as data.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from typing import Any, Callable, Optional

Runner = Callable[..., "subprocess.CompletedProcess[str]"]

TMUX_TIMEOUT_SECONDS = 5

PEEK_DEFAULT_LINES = 200
PEEK_MAX_LINES = 200
PEEK_MAX_BYTES = 64_000

# CSI sequences, OSC strings (BEL- or ST-terminated), charset picks,
# and keypad-mode toggles — everything a `capture-pane -e` snapshot
# carries that a <pre> must not.
_ANSI_RE = re.compile(
    r"\x1b\[[0-9;?]*[a-zA-Z]"
    r"|\x1b\].*?(?:\x07|\x1b\\)"
    r"|\x1b[()][0-9A-B]"
    r"|\x1b[=>]"
)


def _default_runner(
    argv: list[str], cwd: Optional[str] = None
) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TMUX_TIMEOUT_SECONDS,
    )


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def content_hash(text: str) -> str:
    """Stable digest of a pane snapshot — the peek answers
    `not_modified` when this matches the client's last seen."""
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def resolve_pane_target(session: Any) -> Optional[str]:
    """The registry record's pane address.

    Prefer the unique ``%N`` pane id the hook captured; fall back to
    the composed ``session:window.pane`` address; None when the
    record never saw tmux at all.
    """
    pane = getattr(session, "tmux_pane", None)
    if pane:
        return str(pane)
    name = getattr(session, "tmux_session", None)
    window = getattr(session, "tmux_window", None)
    index = getattr(session, "tmux_pane_index", None)
    if name and window is not None and index is not None:
        return f"{name}:{window}.{index}"
    return None


def peek_pane(
    target: str,
    *,
    lines: int = PEEK_DEFAULT_LINES,
    last_hash: Optional[str] = None,
    runner: Optional[Runner] = None,
) -> dict[str, Any]:
    """Read-only snapshot of a pane's last N lines.

    Statuses: ``live`` (hash + lines), ``not_modified`` (hash only —
    the gate that keeps polling cheap), ``pane_gone``, ``tmux_absent``,
    ``error``. Never raises for tmux-shaped failures.
    """
    if runner is None and shutil.which("tmux") is None:
        return {"status": "tmux_absent"}
    run = runner or _default_runner
    try:
        capped = max(1, min(int(lines), PEEK_MAX_LINES))
    except (TypeError, ValueError):
        capped = PEEK_DEFAULT_LINES
    try:
        completed = run(
            [
                "tmux",
                "capture-pane",
                "-p",
                "-e",
                "-t",
                str(target),
                "-S",
                f"-{capped}",
            ]
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "error", "detail": str(exc)}
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or "tmux refused"
        return {"status": "pane_gone", "detail": detail}
    text = strip_ansi(completed.stdout or "").rstrip("\n")
    encoded = text.encode("utf-8", "replace")
    if len(encoded) > PEEK_MAX_BYTES:
        # Keep the tail — the newest output is the point of a peek.
        text = encoded[-PEEK_MAX_BYTES:].decode("utf-8", "replace")
        head_cut = text.find("\n")
        if head_cut != -1:
            text = text[head_cut + 1 :]
    digest = content_hash(text)
    if last_hash and digest == last_hash:
        return {"status": "not_modified", "hash": digest}
    return {"status": "live", "hash": digest, "lines": text.split("\n")}


def awaiting_snapshot(sessions: list[Any]) -> dict[str, bool]:
    """``{key: awaiting_response}`` over the registry — the watcher's
    per-tick view, keyed the way every coder surface keys sessions."""
    return {
        f"{s.agent}:{s.session_id}": bool(s.awaiting_response) for s in sessions
    }


def awaiting_transitions(
    previous: dict[str, bool], current: dict[str, bool]
) -> list[str]:
    """Keys whose awaiting-response flag actually moved.

    A brand-new key counts only when it arrives already awaiting (a
    session starting up is not a transition); a vanished key is a
    prune, not a transition. The first observation is a baseline the
    caller never diffs (the HS-86-03 rule).
    """
    changed: list[str] = []
    for key, awaiting in current.items():
        if key in previous:
            if previous[key] != awaiting:
                changed.append(key)
        elif awaiting:
            changed.append(key)
    return changed


__all__ = [
    "PEEK_DEFAULT_LINES",
    "PEEK_MAX_BYTES",
    "PEEK_MAX_LINES",
    "Runner",
    "TMUX_TIMEOUT_SECONDS",
    "awaiting_snapshot",
    "awaiting_transitions",
    "content_hash",
    "peek_pane",
    "resolve_pane_target",
    "strip_ansi",
]
