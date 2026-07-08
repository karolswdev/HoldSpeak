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
import threading
import time
from typing import Any, Callable, Optional

Runner = Callable[..., "subprocess.CompletedProcess[str]"]
Clock = Callable[[], float]

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


# --- The arming grant (HS-87-02): consent with a countdown ---------------
#
# Watching is free; ANY keystroke toward a pane requires an active
# grant for that session. One file owns consent: the store is
# in-memory and module-level — a hub restart disarms everything (fail
# closed, a phase decision, not a gap). Expiry is a lazy sweep on
# read; there is no background timer. The clock is monotonic so a
# wall-clock jump can never extend a grant.

ARM_DEFAULT_TTL_SECONDS = 15 * 60  # the upstream Telegram default
ARM_MAX_TTL_SECONDS = 60 * 60  # the upstream hard cap
ARM_MIN_TTL_SECONDS = 10

_GRANTS: dict[str, dict[str, Any]] = {}
_GRANTS_LOCK = threading.Lock()


def resolve_pane_identity(
    target: str, *, runner: Optional[Runner] = None
) -> dict[str, Any]:
    """The pane's unique ``%N`` id, freshly resolved from tmux.

    Statuses: ``ok`` (with ``pane_id``), ``pane_gone``, ``tmux_absent``,
    ``error``. This is the recycled-pane lesson made structural: prove
    what the target resolves to NOW, never trust a stored address.
    """
    if runner is None and shutil.which("tmux") is None:
        return {"status": "tmux_absent"}
    run = runner or _default_runner
    try:
        completed = run(
            ["tmux", "display-message", "-p", "-t", str(target), "#{pane_id}"]
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "error", "detail": str(exc)}
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or "tmux refused"
        return {"status": "pane_gone", "detail": detail}
    pane_id = (completed.stdout or "").strip()
    if not pane_id:
        # tmux 3.6 answers a dead target with rc 0 and an EMPTY
        # expansion when the server is otherwise alive — an
        # unprovable pane is a gone pane, never a transient error.
        return {"status": "pane_gone", "detail": "target does not resolve to a pane"}
    return {"status": "ok", "pane_id": pane_id}


def clamp_ttl(ttl_seconds: Any) -> int:
    try:
        ttl = int(ttl_seconds)
    except (TypeError, ValueError):
        return ARM_DEFAULT_TTL_SECONDS
    return max(ARM_MIN_TTL_SECONDS, min(ttl, ARM_MAX_TTL_SECONDS))


def arm(
    key: str,
    target: str,
    *,
    ttl_seconds: int = ARM_DEFAULT_TTL_SECONDS,
    runner: Optional[Runner] = None,
    clock: Clock = time.monotonic,
) -> dict[str, Any]:
    """Issue the grant: pin the pane identity, start the countdown.

    Statuses: ``armed`` (with ``pane_id`` + ``expires_in_seconds``),
    or the identity failure verbatim (``pane_gone`` / ``tmux_absent`` /
    ``error``) — a pane that cannot prove itself cannot be armed.
    """
    identity = resolve_pane_identity(target, runner=runner)
    if identity["status"] != "ok":
        return identity
    ttl = clamp_ttl(ttl_seconds)
    now = clock()
    with _GRANTS_LOCK:
        _GRANTS[key] = {
            "pane_id": identity["pane_id"],
            "target": str(target),
            "granted_at": now,
            "expires_at": now + ttl,
        }
    return {
        "status": "armed",
        "key": key,
        "pane_id": identity["pane_id"],
        "expires_in_seconds": ttl,
    }


def disarm(key: str) -> bool:
    """One tap, immediate; idempotent (returns whether a grant died)."""
    with _GRANTS_LOCK:
        return _GRANTS.pop(key, None) is not None


def sweep_expired(*, clock: Clock = time.monotonic) -> list[str]:
    """Drop every grant past its window; return the keys that expired.
    The caller broadcasts their frames — the sweep is the only timer."""
    now = clock()
    expired: list[str] = []
    with _GRANTS_LOCK:
        for key in list(_GRANTS):
            if now > _GRANTS[key]["expires_at"]:
                del _GRANTS[key]
                expired.append(key)
    return expired


def active_grants(*, clock: Clock = time.monotonic) -> dict[str, dict[str, Any]]:
    """``{key: {pane_id, expires_in_seconds}}`` for every live grant
    (expired ones swept first — call `sweep_expired` yourself when you
    need the expiry keys for frames)."""
    sweep_expired(clock=clock)
    now = clock()
    with _GRANTS_LOCK:
        return {
            key: {
                "pane_id": grant["pane_id"],
                "expires_in_seconds": max(0, int(grant["expires_at"] - now)),
            }
            for key, grant in _GRANTS.items()
        }


def require_grant(
    key: str,
    current_target: Optional[str],
    *,
    runner: Optional[Runner] = None,
    clock: Clock = time.monotonic,
) -> dict[str, Any]:
    """THE chokepoint check — nothing types without passing here.

    Statuses: ``ok`` (grant verified against the pane the registry
    points at NOW), ``unarmed``, ``expired`` (removed), ``pane_gone``
    (REVOKED), ``pane_mismatch`` (REVOKED — the recycled/retargeted
    pane must never receive text meant for its predecessor),
    ``tmux_absent`` / ``error`` (refused, grant kept: transient
    failures burn nothing, and nothing was typed).
    """
    with _GRANTS_LOCK:
        grant = _GRANTS.get(key)
    if grant is None:
        return {"status": "unarmed"}
    if clock() > grant["expires_at"]:
        with _GRANTS_LOCK:
            _GRANTS.pop(key, None)
        return {"status": "expired", "revoked": True}
    if not current_target:
        # The registry lost the pane while the grant lived: structural.
        disarm(key)
        return {"status": "pane_gone", "detail": "registry has no pane", "revoked": True}
    identity = resolve_pane_identity(current_target, runner=runner)
    if identity["status"] == "pane_gone":
        disarm(key)
        return {**identity, "revoked": True}
    if identity["status"] != "ok":
        return identity  # transient: refuse, keep the grant
    if identity["pane_id"] != grant["pane_id"]:
        disarm(key)
        return {
            "status": "pane_mismatch",
            "detail": (
                f"pane {identity['pane_id']!r} is not the armed "
                f"{grant['pane_id']!r} — nothing was typed"
            ),
            "revoked": True,
        }
    return {
        "status": "ok",
        "pane_id": grant["pane_id"],
        "expires_in_seconds": max(0, int(grant["expires_at"] - clock())),
    }


def clear_grants() -> None:
    """Test seam. A real restart clears the store by construction."""
    with _GRANTS_LOCK:
        _GRANTS.clear()


# --- Deliver (HS-87-03): THE chokepoint ------------------------------------
#
# The only path by which steering text reaches a pane. require_grant
# verifies the pinned identity against what the registry points at
# NOW; the send itself targets the verified `%N` (not the target
# string, so nothing can re-resolve between check and keystroke); the
# send craft is `tmux_transport.send_text_to_pane` verbatim — literal
# text, submit as its own raw `\r`. Every attempt lands one audit
# row, refusals included.


def _default_audit(**kw: Any) -> int:
    from . import db as hsdb

    return hsdb.get_database().steering.record(**kw)


def deliver(
    key: str,
    text: str,
    *,
    current_target: Optional[str],
    agent: str = "",
    submit: bool = True,
    grounding_refs: Optional[list[Any]] = None,
    runner: Optional[Runner] = None,
    clock: Clock = time.monotonic,
    transport: Optional[Callable[..., Any]] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """Deliver one steer into an armed session's verified pane.

    Statuses: ``delivered``, ``empty_text``, the `require_grant`
    refusals verbatim (``unarmed`` / ``expired`` / ``pane_mismatch`` /
    ``pane_gone`` / ``tmux_absent`` / ``error``), or
    ``transport_error`` when tmux refused the keystroke itself.
    Every outcome is audited; ``audit_id`` rides the result.
    """
    record = audit or _default_audit
    refs = list(grounding_refs or [])

    def _audited(result: dict[str, Any], *, pane_id: Optional[str]) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=key,
                agent=agent,
                pane_id=pane_id,
                text=text,
                grounding=refs,
                submit=submit,
                outcome=result["status"],
                detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    if not str(text or "").strip():
        return _audited({"status": "empty_text"}, pane_id=None)
    check = require_grant(key, current_target, runner=runner, clock=clock)
    if check["status"] != "ok":
        return _audited(dict(check), pane_id=None)
    pane_id = check["pane_id"]
    send = transport
    if send is None:
        from .tmux_transport import send_text_to_pane

        send = send_text_to_pane
    try:
        send(pane=pane_id, text=text, submit=submit)
    except Exception as exc:
        return _audited(
            {"status": "transport_error", "detail": str(exc)}, pane_id=pane_id
        )
    return _audited(
        {"status": "delivered", "pane_id": pane_id, "submitted": bool(submit)},
        pane_id=pane_id,
    )


__all__ = [
    "ARM_DEFAULT_TTL_SECONDS",
    "ARM_MAX_TTL_SECONDS",
    "ARM_MIN_TTL_SECONDS",
    "Clock",
    "PEEK_DEFAULT_LINES",
    "PEEK_MAX_BYTES",
    "PEEK_MAX_LINES",
    "Runner",
    "TMUX_TIMEOUT_SECONDS",
    "arm",
    "active_grants",
    "awaiting_snapshot",
    "awaiting_transitions",
    "clamp_ttl",
    "clear_grants",
    "content_hash",
    "deliver",
    "disarm",
    "peek_pane",
    "require_grant",
    "resolve_pane_identity",
    "resolve_pane_target",
    "strip_ansi",
    "sweep_expired",
]
