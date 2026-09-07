"""The database owner lock (HS-200-02, contracts C1 and C10).

Two ``holdspeak web`` processes used to run against one database file and
neither reported the other (observed live on 2026-09-06: pid 63921 on :54644
and pid 81866 on :49353, both holding
``~/.local/share/holdspeak/holdspeak.db``). Both ran the heartbeat sweep.
C1 forbids exactly that — "Two processes cannot silently own the same
scheduled work" — and C10 forbids introducing a multi-writer SQLite
arrangement at all.

The guard is an OS lock on a sibling file, the same shape the mesh worker
already uses (``holdspeak/db/mesh_worker.py``): ``flock(LOCK_EX | LOCK_NB)``
on ``<database>.owner.lock``. An OS lock is the right primitive because it
releases on process exit of *any* kind — a crash, a SIGKILL, a power loss —
so a stale claim cannot outlive its process. The JSON body (pid, start, port)
exists only so the refusal can *name* the owner; liveness is confirmed against
the pid, never trusted from the file.

**The chosen behaviour: the second hub refuses to start.** A read-only second
hub is not the safer option here: every POST route on it would still be a
second writer to one SQLite file, which is the arrangement C10 rejects
outright, and a degraded hub invites a user to keep working in a window whose
writes race the real owner. Refusing is loud, immediate, and reaches the person
who just typed the command. The escape hatch ``HOLDSPEAK_ALLOW_UNOWNED_DB=1``
starts anyway **without** the scheduled sweeps and flies a ``TWO RUNTIMES``
repair state on the Desk; it exists for a diagnosis session, not for daily use.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("runtime_lock")

LOCK_SUFFIX = ".owner.lock"

#: Start anyway when another hub owns the database. The sweeps stay off and the
#: Desk shows TWO RUNTIMES. A diagnosis hatch, never the daily path.
ALLOW_UNOWNED_ENV = "HOLDSPEAK_ALLOW_UNOWNED_DB"


def owner_lock_path(db_path: Path) -> Path:
    """The lock file beside a database."""
    p = Path(db_path).expanduser()
    return p.with_name(p.name + LOCK_SUFFIX)


def pid_alive(pid: Any) -> bool:
    """Whether a pid names a live process on this machine."""
    try:
        value = int(pid)
    except (TypeError, ValueError):
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Alive and owned by somebody else.
        return True
    except OSError:  # pragma: no cover - platform oddity
        return False
    return True


def read_owner(db_path: Path) -> Optional[dict[str, Any]]:
    """The recorded owner of a database, with liveness resolved.

    Returns ``None`` when no lock file exists or it is unreadable. A record
    whose pid is dead comes back with ``alive: False`` — that is a *stale*
    claim, and the caller may take the lock over it.
    """
    path = owner_lock_path(db_path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    data = dict(data)
    data["alive"] = pid_alive(data.get("pid"))
    return data


class DatabaseOwnerLock:
    """An exclusive, process-lifetime claim on one database file."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path).expanduser()
        self.path = owner_lock_path(self.db_path)
        self._handle: Optional[int] = None
        self._owner: Optional[dict[str, Any]] = None

    # ── state ────────────────────────────────────────────────────────

    @property
    def held(self) -> bool:
        return self._handle is not None

    def owner(self) -> Optional[dict[str, Any]]:
        """Who holds it — this process when held, else the recorded claimant."""
        if self.held:
            return dict(self._owner or {})
        return read_owner(self.db_path)

    def snapshot(self) -> dict[str, Any]:
        """The payload the identity surfaces carry."""
        return {
            "held": self.held,
            "lock_path": str(self.path),
            "owner": self.owner(),
        }

    # ── acquire / release ────────────────────────────────────────────

    def acquire(
        self,
        *,
        port: Optional[int] = None,
        host: Optional[str] = None,
        process_start: Optional[str] = None,
    ) -> bool:
        """Claim the database. ``False`` means a live hub already owns it.

        The claim is written only after the OS lock is granted, so a refused
        process can never overwrite the real owner's record.
        """
        if self.held:
            self._write_claim(port=port, host=host, process_start=process_start)
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(str(self.path), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(handle)
                return False
        except ImportError:  # pragma: no cover - platform without fcntl
            log.warning("runtime_lock: fcntl unavailable; database ownership unguarded")
        self._handle = handle
        self._write_claim(port=port, host=host, process_start=process_start)
        return True

    def release(self) -> None:
        """Drop the claim. Safe to call when not held, and never raises."""
        handle, self._handle = self._handle, None
        self._owner = None
        if handle is None:
            return
        try:
            os.close(handle)
        except OSError:  # pragma: no cover
            pass

    def _write_claim(
        self,
        *,
        port: Optional[int],
        host: Optional[str],
        process_start: Optional[str],
    ) -> None:
        self._owner = {
            "pid": os.getpid(),
            "process_start": process_start or datetime.now().isoformat(),
            "port": port,
            "host": host,
        }
        if self._handle is None:  # pragma: no cover - fcntl-less fallback
            return
        body = json.dumps(self._owner, indent=2).encode("utf-8")
        try:
            os.lseek(self._handle, 0, os.SEEK_SET)
            os.ftruncate(self._handle, 0)
            os.write(self._handle, body)
            os.fsync(self._handle)
        except OSError as exc:  # pragma: no cover - never fail a boot on the note
            log.warning(f"runtime_lock: could not record the owner claim ({exc})")


# ── The process-wide claim ───────────────────────────────────────────

_LOCK: Optional[DatabaseOwnerLock] = None


def claim_database(
    db_path: Path,
    *,
    port: Optional[int] = None,
    host: Optional[str] = None,
    process_start: Optional[str] = None,
) -> DatabaseOwnerLock:
    """Claim ``db_path`` for this process and remember the claim.

    Idempotent per path: a process that already holds this database keeps the
    claim it has. Without this a second ``claim_database`` in one process would
    open a second descriptor on the same file, and ``flock`` would refuse the
    process its own lock — a hub reporting TWO RUNTIMES against itself.
    """
    global _LOCK
    path = Path(db_path).expanduser()
    if _LOCK is not None and _LOCK.held and _LOCK.db_path == path:
        _LOCK.acquire(port=port, host=host, process_start=process_start)
        return _LOCK
    lock = DatabaseOwnerLock(path)
    lock.acquire(port=port, host=host, process_start=process_start)
    _LOCK = lock
    return lock


def current_lock() -> Optional[DatabaseOwnerLock]:
    return _LOCK


def release_database() -> None:
    global _LOCK
    if _LOCK is not None:
        _LOCK.release()
    _LOCK = None


def ownership_snapshot() -> dict[str, Any]:
    """Ownership as the identity surfaces report it.

    A process that never claimed reports ``held: None`` — unknown, not owned
    and not refused. Only a real refusal is a TWO RUNTIMES finding.
    """
    if _LOCK is None:
        return {"held": None, "lock_path": None, "owner": None}
    return _LOCK.snapshot()


def allow_unowned() -> bool:
    return (os.environ.get(ALLOW_UNOWNED_ENV) or "").strip() not in ("", "0", "false", "no")


def refusal_message(db_path: Path, owner: Optional[dict[str, Any]]) -> str:
    """The specific TWO RUNTIMES diagnosis, for the terminal that just refused."""
    lines = [
        "TWO RUNTIMES — another HoldSpeak hub already owns this database.",
        f"  database: {Path(db_path).expanduser()}",
    ]
    if owner:
        lines.append(f"  owner pid: {owner.get('pid')}")
        if owner.get("port"):
            lines.append(f"  owner url: http://{owner.get('host') or '127.0.0.1'}:{owner.get('port')}")
        if owner.get("process_start"):
            lines.append(f"  owner started: {owner.get('process_start')}")
    lines.append("  Stop that hub, or open the one already running.")
    return "\n".join(lines)
