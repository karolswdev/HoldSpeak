"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from ..logging_config import get_logger
from .base import BaseRepository
from .connection import (
    ConnectionCache,
    make_connection_factory,
    connection as _raw_connection,  # noqa: F401  re-exported for callers
)

# Import every repository module so __init_subclass__ fires and the registry
# fills before Database.__init__ iterates it.
from .activity import ActivityRepository as _c0  # noqa: F401
from . import (  # noqa: F401
    actuators as _m1, cadence as _m2, corrections as _m3,
    decisions as _m4, delivery_attempts as _m5, delivery_receipts as _m6,
    desktop_typing as _m7, dictation_delivery as _m8, gate as _m9,
    intel as _m10, invocations as _m11, journal as _m12,
    meetings as _m13, memory as _m14, mesh_relay as _m15,
    milestones as _m16, onboarding as _m17, plugins as _m18,
    primitives as _m19, projects as _m20, projections as _m21,
    relationships as _m22, steering as _m23, workbenches as _m24,
    automations as _m25, resourceful as _m26,
    scheduled_recordings as _m27, refinement_thoughts as _m28,
    calendar_events as _m29, threads as _m30,
    front_door as _m31, delta as _m32,
    updates as _m33,
    steward as _m34,
    proposals as _m35,
)

from .schema import SCHEMA_VERSION, SCHEMA_SQL  # noqa: F401  re-exported
from .reconcile import reconcile_schema

log = get_logger("db")

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"


def read_schema_version(db_path: Path) -> Optional[int]:
    """Return a database's stored schema version without opening it for use.

    A missing file or a missing/empty ``schema_version`` table reads as None (a
    fresh database). Read-only probe: never creates the file, never runs
    ``_ensure_schema``.
    """
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        try:
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        except sqlite3.DatabaseError:
            return None
        if not row or row[0] is None:
            return None
        return int(row[0])
    finally:
        conn.close()


def _timestamped_backup_path(db_path: Path) -> Path:
    """A non-clobbering, timestamped backup path next to the database."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.{timestamp}.bak")
    counter = 1
    while backup_path.exists():
        backup_path = db_path.with_name(f"{db_path.name}.{timestamp}-{counter}.bak")
        counter += 1
    return backup_path


def backup_database(db_path: Path) -> Path:
    """Snapshot the SQLite database to a timestamped sibling and return it."""
    backup_path = _timestamped_backup_path(db_path)
    source = sqlite3.connect(str(db_path))
    try:
        dest = sqlite3.connect(str(backup_path))
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()
    return backup_path


def restore_database(backup_path: Path, db_path: Path) -> Optional[Path]:
    """Restore ``db_path`` from ``backup_path``, returning the safety backup taken."""
    if not backup_path.exists():
        raise ValueError(f"Backup file not found: {backup_path}")
    probe = sqlite3.connect(str(backup_path))
    try:
        try:
            row = probe.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='meetings'"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise ValueError(
                f"{backup_path} is not a readable HoldSpeak database backup ({exc})."
            ) from exc
        if not row:
            raise ValueError(
                f"{backup_path} is not a HoldSpeak database (missing 'meetings' table)."
            )
    finally:
        probe.close()
    safety: Optional[Path] = None
    if db_path.exists():
        safety = backup_database(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)
    return safety


class Database:
    """SQLite database manager for meeting persistence.

    Repository instances are created automatically from
    :data:`BaseRepository._registry` populated by ``__init_subclass__``.
    Every registered ``table`` name becomes an attribute (e.g. ``db.meetings``).
    """

    if TYPE_CHECKING:
        # Stubs so IDEs resolve attribute access on Database instances.
        from .meetings import MeetingRepository
        from .intel import IntelRepository
        from .plugins import PluginArtifactRepository
        from .projects import ProjectRepository
        from .activity import ActivityRepository
        from .calendar_events import CalendarEventRepository
        from .threads import ThreadRepository
        meetings: MeetingRepository
        intel: IntelRepository
        plugins: PluginArtifactRepository
        projects: ProjectRepository
        activity: ActivityRepository
        calendar_events: CalendarEventRepository
        threads: ThreadRepository

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        # One warm connection per thread, owned by this instance alone (HS-131-09).
        self._conn_cache = ConnectionCache(self.db_path)
        self._conn_factory = make_connection_factory(self.db_path, self._conn_cache)
        self._ensure_schema()
        for table_name, repo_cls in BaseRepository._registry.items():
            setattr(self, table_name, repo_cls(self._conn_factory, self))

    def _connection(self):
        """Context manager for database connections."""
        return self._conn_cache.connection()

    def close(self) -> None:
        """Release this instance's cached connections. Safe to call twice."""
        cache = getattr(self, "_conn_cache", None)
        if cache is not None:
            cache.close()

    def __del__(self) -> None:  # pragma: no cover - GC timing
        try:
            self.close()
        except Exception:
            pass

    def _ensure_schema(self) -> None:
        """Bring the database to the canonical schema shape unconditionally.

        Uses the declarative reconcile (HS-137-01): no version gate, no
        ``SchemaVersionError``.  Idempotent and additive-only.  Backs up
        the DB file before any shape change; data backfills run only when
        the shape actually changed.
        """
        with self._connection() as conn:
            reconcile_schema(conn, db_path=self.db_path)
            from .refinement_thoughts import RefinementThoughtRepository
            RefinementThoughtRepository.reconcile_legacy_ledgers(conn)
            RefinementThoughtRepository.reconcile_resume_orders(conn)
            RefinementThoughtRepository.reconcile_missing_working_notes(conn)


_db: Optional[Database] = None
_observer: Optional[Any] = None

# HS-200-03: one lock over the singleton's whole lifecycle.
#
# `get_database` was a check-then-assign around a constructor that takes a
# quarter of a second (it opens the file, reconciles the schema and builds
# every repository). Two threads could therefore both see `_db is None` and
# both build a Database over the same file, running `reconcile_schema`
# concurrently; and a construction already in flight would publish its result
# AFTER a `reset_database()` that ran in the meantime, silently restoring a
# database the caller had just dropped — including one resolved from a path
# captured before the reset.
#
# The hub runs long-lived conductor threads that call `get_database()` on a
# timer, so this was not theoretical: it is the mechanism behind the three
# CI-only `tests/integration/test_web_activity_api.py` failures on Actions run
# 34007939416, where a conductor tick landing inside a test's setup window
# published a foreign database to the routes under test. It is also a
# production hazard on any in-process restart.
#
# The lock is reentrant because `get_observer` calls `get_database` while
# holding it.
_db_lock = threading.RLock()


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get or create the database singleton."""
    global _db
    with _db_lock:
        if _db is None:
            _db = Database(db_path)
        return _db


def get_observer() -> Any:
    """Get or create the pipeline observer singleton.

    Returns a SQLiteObserver wired to the database singleton's connection.
    """
    global _observer
    with _db_lock:
        if _observer is None:
            from holdspeak.services.sqlite_observer import SQLiteObserver
            _observer = SQLiteObserver(get_database()._connection)
        return _observer


def reset_database() -> None:
    """Reset the database singleton (for testing)."""
    global _db, _observer
    with _db_lock:
        if _db is not None:
            try:
                _db.close()
            except Exception:
                pass
        _db = None
        _observer = None
