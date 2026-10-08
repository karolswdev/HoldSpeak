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

import os
import re
import shutil
import signal
import subprocess
import time
import uuid
from pathlib import Path
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
    launch_id: Optional[str] = None,
    scope_items: tuple[str, ...] = (),
    project_id: Optional[str] = None,
    model_key: Optional[str] = None,
    runner: Optional[Runner] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """Create a detached tmux session `name` (optionally running `command`),
    and return its first pane. Statuses: ``spawned``, ``bad_name``,
    ``tmux_absent``, ``exists``, ``error``. Audited.

    Conductor K6: a spawn for an agent launch (``launch_id``) issues a
    launch-bound credential, identity ``agent:launch:<launch_id>``, with the
    CONDUCTOR palette: the launched agent reaches the HoldSpeak MCP from this
    machine with the Reach switch off. Revoked when the session ends (the
    rider's SessionEnd self-revoke, ``kill``), on cleanup and on a failed
    launch (``revoke_launch``)."""
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
    from .principals import CredentialPersistError, agent_credentials

    launch = str(launch_id or "").strip()
    identity = launch_identity(launch) if launch else f"agent:tmux:{name}"
    try:
        if launch:
            from .mcp.palettes import CONDUCTOR, resolve_palette

            credential = agent_credentials.issue(
                identity,
                palette=resolve_palette(CONDUCTOR),
                palette_name=CONDUCTOR,
                launch_id=launch,
                scope_items=scope_items,  # the launch's origin item
                project_id=project_id,  # the launch's own Project
            )
        else:
            credential = agent_credentials.issue(identity)
    except CredentialPersistError as exc:
        return _audited({"status": "error", "detail": f"credential not stored: {exc}"})

    def _fail(status: str, detail: str, env_file: Optional[Path] = None) -> dict[str, Any]:
        agent_credentials.revoke(identity, "spawn_failed")
        if env_file is not None:
            _discard(env_file)
        return _audited({"status": status, "detail": detail})

    # The supervised agent receives only its scoped token, never the owner's
    # browser credential. Conductor R2: the token never rides argv (``ps``
    # shows argv) and is never read by a shell that traces: a 0600 file in a
    # 0700 directory carries it; tmux runs the bootstrap directly (no user
    # shell, no rc file), which turns tracing off, reads the file with
    # ``read``, deletes it and only then execs the user's shell.
    try:
        env_file = write_credential_env(credential.token, model_key=model_key)
    except (OSError, ValueError) as exc:
        return _fail("error", f"credential file: {type(exc).__name__}")
    argv = [
        "tmux",
        "new-session",
        "-d",
        "-e",
        f"HOLDSPEAK_HUB_URL={agent_credentials.hub_url}",
        "-s",
        name,
        *session_argv(env_file, command),
    ]
    try:
        completed = _run(runner, argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _fail("error", str(exc), env_file)
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip()
        status = "exists" if "duplicate" in detail.lower() else "error"
        return _fail(status, detail or "tmux refused", env_file)
    # The session read its credential: the file is gone. A session that did
    # not start (or exited first) is not reported spawned.
    if not _consumed(env_file, START_TIMEOUT_SECONDS):
        return _fail("error", "the session did not start: it did not read its credential", env_file)
    # The session must still be there, with a live pane: a shell that exited
    # after the bootstrap read the file is not a launch (a short settle lets
    # an rc file that exits at once be seen).
    if START_SETTLE_SECONDS > 0:
        time.sleep(START_SETTLE_SECONDS)
    try:
        panes = _run(runner, ["tmux", "list-panes", "-t", name, "-F", "#{pane_id} #{pane_dead}"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _fail("error", f"the session is gone: {exc}")
    first = (panes.stdout or "").strip().splitlines()[0].split() if (panes.stdout or "").strip() else []
    if panes.returncode != 0 or not first or not first[0].startswith("%") or first[1:2] == ["1"]:
        return _fail("error", "the session ended before the agent started")
    pane_id = first[0]
    try:
        agent_credentials.bind_target(identity, name, pane_id)
    except CredentialPersistError as exc:
        return _fail("error", f"credential not stored: {exc}")
    return _audited({"status": "spawned", "session": name, "pane_id": pane_id}, pane_id)


#: The environment variable the session's processes read the token from.
CREDENTIAL_ENV = "HOLDSPEAK_AGENT_CREDENTIAL"

#: How long a new session has to read its credential file.
START_TIMEOUT_SECONDS = 15.0

#: After the read, how long the session's shell has to prove it stays up.
START_SETTLE_SECONDS = 0.3

#: The environment variable a pi launch reads its engine's key from (the
#: second line of the one-shot file; ``delivery.pi_launch``).
MODEL_KEY_ENV = "HOLDSPEAK_PI_MODEL_KEY"

#: The session's first process: run by tmux directly, never by the user's
#: shell. ``$1`` is the credential file, ``$2`` the command ("" = a login
#: shell). /bin/sh -c reads no rc file; tracing is off before the read. The
#: file's first line is the credential; a second line, when there is one, is
#: the launch's model key.
BOOTSTRAP = (
    "set +xv; "
    f'{{ IFS= read -r {CREDENTIAL_ENV} || exit 97; IFS= read -r {MODEL_KEY_ENV} || {MODEL_KEY_ENV}=; }} < "$1" || exit 97; '
    'rm -f "$1"; '
    f"export {CREDENTIAL_ENV}; "
    f'if [ -n "${MODEL_KEY_ENV}" ]; then export {MODEL_KEY_ENV}; else unset {MODEL_KEY_ENV}; fi; '
    'if [ -n "$2" ]; then exec "${SHELL:-/bin/sh}" -c "$2"; fi; '
    'exec "${SHELL:-/bin/sh}" -l'
)


def credential_env_dir() -> Path:
    """The private directory of the one-shot credential files (0700)."""
    return Path.home() / ".holdspeak" / "agent-env"


def write_credential_env(
    token: str, directory: Optional[Path] = None, *, model_key: Optional[str] = None,
) -> Path:
    """Write ``token`` (one line, no shell syntax) to a new 0600 file the
    session's bootstrap reads once, and ``model_key`` as its second line when
    given. A partial write is removed."""
    lines = [token]
    if model_key:
        if any(ch in model_key for ch in "\r\n\0"):
            raise ValueError("the model key is not one line")
        lines.append(model_key)
    folder = directory or credential_env_dir()
    folder.mkdir(parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    target = folder / f"{uuid.uuid4().hex}.cred"
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        try:
            os.write(fd, ("\n".join(lines) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        _discard(target)
        raise
    return target


def session_argv(env_file: Path, command: Optional[str]) -> list[str]:
    """The session's command as separate words: tmux runs it directly."""
    return ["/bin/sh", "-c", BOOTSTRAP, "holdspeak-agent", str(env_file), command or ""]


def _consumed(path: Path, timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if not path.exists():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


def _discard(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def launch_identity(launch_id: str) -> str:
    """The principal identity of a launch-bound agent credential."""
    return f"agent:launch:{str(launch_id).strip()}"


def revoke_launch(launch_id: str) -> bool:
    """Revoke the launch-bound credential of one launch (idempotent)."""
    from .principals import agent_credentials

    clean = str(launch_id or "").strip()
    return bool(clean) and agent_credentials.revoke(launch_identity(clean))


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
        refused = dict(check)
        if runner is None and current_target and not _pane_exists(str(current_target)):
            # PR #1022 r1: the pane closed with its first process, but the
            # children the launch started (a hook that waits on a hold) can
            # live on: the group the launch recorded at spawn is ended.
            groups = _recorded_groups(str(current_target))
            if groups:
                left = _end_groups(groups)
                refused["launch_processes"] = "survived" if left else "ended"
        return _audited(refused)
    pane_id = check["pane_id"]
    argv = (
        ["tmux", "kill-session", "-t", pane_id] if scope == "session"
        else ["tmux", "kill-pane", "-t", pane_id]
    )
    # pi spike #1020: a hook child that waits on a gate hold outlived its
    # agent. The launch's process groups are read first: the group the launch
    # recorded at spawn (PR #1022 r1: also when the pane's first process has
    # already exited) and each live pane's group. After tmux ends the pane,
    # each member of those groups that is still in the recorded session gets
    # SIGTERM, then SIGKILL after the grace; the kill is reported only when no
    # member is left. Only against the real tmux: an injected runner (a
    # test's fake) names no real process.
    groups = _kill_groups(pane_id, scope) if runner is None else []
    try:
        completed = _run(runner, argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": str(exc)}, pane_id)
    if completed.returncode != 0:
        return _audited(
            {"status": "error", "detail": (completed.stderr or "").strip() or "tmux refused"},
            pane_id,
        )
    survivors = _end_groups(groups)
    # The pane is gone: the grant and its process credential can never be
    # reused.  Respawning the name mints a distinct token.
    coder_steering.disarm(key)
    from .principals import agent_credentials

    agent_credentials.revoke_targets((pane_id, current_target, key))
    if survivors:
        return _audited({
            "status": "error", "pane_id": pane_id, "scope": scope,
            "detail": f"{len(survivors)} process(es) of the launch did not end",
        }, pane_id)
    return _audited({"status": "killed", "pane_id": pane_id, "scope": scope}, pane_id)


#: How long a killed pane's process group has to end after SIGTERM before SIGKILL.
GROUP_KILL_GRACE_SECONDS = 2.0

#: One process group to end: ``(pgid, sid)``. A member is a process in that
#: group AND that session, so a recycled id never names another program.
Group = tuple[int, int]


def pane_process_group(pane_id: str, *, runner: Optional[Runner] = None) -> Optional[dict[str, int]]:
    """``{pgid, sid, leader}`` of a live pane's first process, read at spawn
    so Stop can end the group after that process has exited (PR #1022 r1).
    ``None`` for a fake runner, a dead pane, or this process's own group."""
    if runner is not None:
        return None
    try:
        done = _run(None, ["tmux", "display-message", "-p", "-t", str(pane_id), "#{pane_pid}"])
        leader = int(str(done.stdout or "").strip()) if done.returncode == 0 else 0
        if leader <= 1:
            return None
        pgid, sid = os.getpgid(leader), os.getsid(leader)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    if pgid <= 1 or pgid == os.getpgrp():
        return None
    return {"pgid": pgid, "sid": sid, "leader": leader}


def _pane_exists(pane_id: str) -> bool:
    try:
        done = _run(None, ["tmux", "display-message", "-p", "-t", str(pane_id), "#{pane_id}"])
    except (OSError, subprocess.TimeoutExpired):
        return True  # not known: never reap on a guess
    return done.returncode == 0 and str(done.stdout or "").strip() == str(pane_id)


def _kill_groups(pane_id: str, scope: str) -> list[Group]:
    groups = _recorded_groups(pane_id)
    for group in _pane_groups(None, pane_id, scope):
        if group not in groups:
            groups.append(group)
    return groups


def _recorded_groups(pane_id: str) -> list[Group]:
    """The groups launches recorded at spawn for this pane's tmux session."""
    # The pane's session when tmux still has it; a pane that is gone is
    # matched by its id alone (the session check on each member still holds).
    try:
        done = _run(None, ["tmux", "display-message", "-p", "-t", str(pane_id), "#{session_name}"])
        session = str(done.stdout or "").strip() if done.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        session = ""
    try:
        from .delivery.factory_launch import LaunchLedger

        rows = LaunchLedger().list()
    except Exception:
        return []
    groups: list[Group] = []
    own = os.getpgrp()
    for row in rows:
        recorded = row.get("process_group")
        if (session and row.get("session") != session) or not isinstance(recorded, dict):
            continue
        if str((row.get("target") or {}).get("pane_id") or "") != str(pane_id):
            continue
        try:
            group = (int(recorded["pgid"]), int(recorded["sid"]))
        except (KeyError, TypeError, ValueError):
            continue
        if group[0] > 1 and group[0] != own and group not in groups:
            groups.append(group)
    return groups


def _pane_groups(runner: Optional[Runner], pane_id: str, scope: str) -> list[Group]:
    """The process groups of the pane (or of its whole session) whose first
    process still lives. Never this process's own group."""
    fmt = "#{pane_pid}"
    argv = (
        ["tmux", "list-panes", "-s", "-t", pane_id, "-F", fmt] if scope == "session"
        else ["tmux", "display-message", "-p", "-t", pane_id, fmt]
    )
    try:
        completed = _run(runner, argv)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if getattr(completed, "returncode", 1) != 0:
        return []
    groups: list[Group] = []
    own = os.getpgrp()
    for line in str(getattr(completed, "stdout", "") or "").splitlines():
        text = line.strip()
        if not text.isdigit():
            continue
        try:
            group = (os.getpgid(int(text)), os.getsid(int(text)))
        except (OSError, ValueError):
            continue
        if group[0] > 1 and group[0] != own and group not in groups:
            groups.append(group)
    return groups


def _members(groups: list[Group]) -> list[int]:
    """The live processes of ``groups``: in the group and in its session."""
    if not groups:
        return []
    try:
        done = subprocess.run(["ps", "-A", "-o", "pid=,pgid="], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return []
    wanted = dict(groups)
    found: list[int] = []
    for line in (done.stdout or "").splitlines():
        parts = line.split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            continue
        pid, pgid = int(parts[0]), int(parts[1])
        if pgid not in wanted or pid == os.getpid():
            continue
        try:
            if os.getsid(pid) == wanted[pgid]:
                found.append(pid)
        except OSError:
            continue
    return found


def _signal(pids: list[int], sig: int) -> None:
    for pid in pids:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def _end_groups(groups: list[Group]) -> list[int]:
    """SIGTERM every member, SIGKILL what is left after the grace; returns
    the members still alive after that (empty: the launch's work ended)."""
    alive = _members(groups)
    if not alive:
        return []
    _signal(alive, signal.SIGTERM)
    deadline = time.monotonic() + GROUP_KILL_GRACE_SECONDS
    while alive and time.monotonic() < deadline:
        time.sleep(0.05)
        alive = _members(groups)
    if alive:
        _signal(alive, signal.SIGKILL)
        deadline = time.monotonic() + GROUP_KILL_GRACE_SECONDS
        while alive and time.monotonic() < deadline:
            time.sleep(0.05)
            alive = _members(groups)
    return alive


__all__ = ["NAME_RE", "kill", "launch_identity", "pane_process_group", "rename", "revoke_launch", "spawn", "valid_name"]
