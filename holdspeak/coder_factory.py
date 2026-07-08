"""The session factory (HS-90-01) — the lifecycle half of taking over the
terminal.

Phase 89 manipulates panes that already exist; the factory creates, relabels,
and ends them. It rides the SAME discipline:

- **spawn / rename** are create/label acts — there is no pane to pin yet, so
  they are explicit + audited, and INJECTION-SAFE: a session name is user
  input, held to a strict allow-list and passed as its own argv slot, never a
  shell string.
- **kill** is the ultimate manipulation, so it is gated exactly like a steer:
  it requires an arming grant, re-verifies the pinned pane `%N`, refuses AND
  revokes on a recycled pane, and audits — reusing `coder_steering`'s spine
  verbatim.

Nothing autonomous; a human is behind every act.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import time
from typing import Any, Callable, Optional

from . import coder_steering
from .coder_steering import Clock, Runner

# A session name is user input: strict allow-list, so it can never carry a
# shell metachar, a space, or a flag. The first char must be alnum/underscore
# so a name can never be read as a tmux flag (`-x`) or a dotfile. Everything
# else refuses BY NAME.
NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")


def _run(runner: Optional[Runner], argv: list[str]) -> "subprocess.CompletedProcess[str]":
    run = runner or coder_steering._default_runner
    return run(argv)


def valid_name(name: str) -> bool:
    return bool(NAME_RE.match(str(name or "")))


def spawn(
    name: str,
    *,
    command: Optional[str] = None,
    runner: Optional[Runner] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """Create a detached tmux session `name` (optionally running `command`),
    and return its first pane. Statuses: ``spawned``, ``bad_name``,
    ``tmux_absent``, ``exists``, ``error``. Audited."""
    record = audit or coder_steering._default_audit

    def _audited(result: dict[str, Any], pane_id: Optional[str] = None) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=f"factory:{name}", agent="factory", pane_id=pane_id,
                text=f"spawn {name}" + (f" :: {command}" if command else ""),
                grounding=[], submit=False, outcome=result["status"],
                detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    if not valid_name(name):
        return _audited({"status": "bad_name", "detail": f"invalid session name: {name!r}"})
    if runner is None and shutil.which("tmux") is None:
        return _audited({"status": "tmux_absent"})
    # `command` is tmux's own trailing arg (its own argv slot) — tmux runs it;
    # we never build a shell string around it.
    argv = ["tmux", "new-session", "-d", "-s", name]
    if command:
        argv.append(command)
    try:
        completed = _run(runner, argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": str(exc)})
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip()
        status = "exists" if "duplicate" in detail.lower() else "error"
        return _audited({"status": status, "detail": detail or "tmux refused"})
    try:
        panes = _run(runner, ["tmux", "list-panes", "-t", name, "-F", "#{pane_id}"])
        pane_id = (panes.stdout or "").strip().splitlines()[0] if panes.stdout else None
    except (OSError, subprocess.TimeoutExpired, IndexError):
        pane_id = None
    return _audited({"status": "spawned", "session": name, "pane_id": pane_id}, pane_id)


def rename(
    target: str,
    new_name: str,
    *,
    runner: Optional[Runner] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """Relabel session `target` to `new_name`. Statuses: ``renamed``,
    ``bad_name``, ``tmux_absent``, ``error``. Audited."""
    record = audit or coder_steering._default_audit

    def _audited(result: dict[str, Any]) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=f"factory:{target}", agent="factory", pane_id=None,
                text=f"rename {target} -> {new_name}", grounding=[], submit=False,
                outcome=result["status"], detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    if not valid_name(new_name):
        return _audited({"status": "bad_name", "detail": f"invalid session name: {new_name!r}"})
    if runner is None and shutil.which("tmux") is None:
        return _audited({"status": "tmux_absent"})
    try:
        completed = _run(runner, ["tmux", "rename-session", "-t", str(target), new_name])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": str(exc)})
    if completed.returncode != 0:
        return _audited({"status": "error", "detail": (completed.stderr or "").strip() or "tmux refused"})
    return _audited({"status": "renamed", "session": new_name})


def kill(
    key: str,
    *,
    current_target: Optional[str],
    scope: str = "pane",
    agent: str = "",
    runner: Optional[Runner] = None,
    clock: Clock = time.monotonic,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """End the armed session's verified pane (``scope="pane"``) or its whole
    session (``scope="session"``). Gated exactly like a steer: requires the
    grant, re-verifies the pinned `%N`, refuses AND revokes a recycled pane.
    Statuses: ``killed``, the `require_grant` refusals verbatim, or
    ``error``. Audited."""
    record = audit or coder_steering._default_audit
    scope = "session" if str(scope) == "session" else "pane"

    def _audited(result: dict[str, Any], pane_id: Optional[str] = None) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=key, agent=agent, pane_id=pane_id,
                text=f"kill {pane_id or '?'} ({scope})", grounding=[], submit=False,
                outcome=result["status"], detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    check = coder_steering.require_grant(key, current_target, runner=runner, clock=clock)
    if check["status"] != "ok":
        return _audited(dict(check))
    pane_id = check["pane_id"]
    argv = (
        ["tmux", "kill-session", "-t", pane_id] if scope == "session"
        else ["tmux", "kill-pane", "-t", pane_id]
    )
    try:
        completed = _run(runner, argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": str(exc)}, pane_id)
    if completed.returncode != 0:
        return _audited(
            {"status": "error", "detail": (completed.stderr or "").strip() or "tmux refused"},
            pane_id,
        )
    # The pane is gone: the grant can never re-verify it, so drop it.
    coder_steering.disarm(key)
    return _audited({"status": "killed", "pane_id": pane_id, "scope": scope}, pane_id)


__all__ = ["NAME_RE", "kill", "rename", "spawn", "valid_name"]
