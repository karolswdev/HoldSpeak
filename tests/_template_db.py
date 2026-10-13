"""One schema template per test process: a new test database is a file copy.

A new ``Database()`` file cost about 56 ms, mostly ``executescript(SCHEMA_SQL)``
over 286 tables, and the FAST suite makes thousands of them (2026-10-12: 23 of
45 s in two DB-heavy files). In tests only, the first new database of a
process is built by the real path (``Database._ensure_schema``) and kept as a
template. A later ``Database(path)`` on a path that does not exist copies the
template file there and skips the schema script.

Product behaviour does not change: the patch lives here and is installed by
``tests/conftest.py``. A copy is the same database a fresh create makes:

* the schema is the same (``tests/unit/test_template_db.py`` compares
  ``sqlite_master`` of a copy and a fresh create, so a schema change cannot
  desync it; the template is built from the current code each run);
* each per-database random or time value is made again on the copy, as a
  fresh create makes it (``RESTAMPED``; the guard test finds a new one).

A copy is made only when the path does not exist; the copy opens the file
with ``"xb"``, so it can never write over a database. A test that proves
schema creation or reconcile on a new file marks itself
``@pytest.mark.real_schema`` and runs the real path.
``HOLDSPEAK_TEST_TEMPLATE_DB=0`` turns the template off for a whole run.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

#: The (table, column) values a fresh create makes new each time, with the
#: SQL that makes them again on a copy. ``?`` takes the Python value from
#: ``_python_value`` (the product writes those stamps from Python).
RESTAMPED: dict[tuple[str, str], str] = {
    ("refinement_workspace_identity", "hub_id"):
        "UPDATE refinement_workspace_identity SET hub_id = 'hub_' || lower(hex(randomblob(16))) WHERE id = 1",
    ("activity_privacy_settings", "updated_at"):
        "UPDATE activity_privacy_settings SET updated_at = datetime('now') WHERE id = 1",
    ("refinement_default_context_revisions", "created_at"):
        "UPDATE refinement_default_context_revisions SET created_at = datetime('now') WHERE revision = 0",
    ("refinement_default_context_current", "updated_at"):
        "UPDATE refinement_default_context_current SET updated_at = datetime('now') WHERE id = 1",
    ("schema_version", "applied_at"):
        "UPDATE schema_version SET applied_at = datetime('now')",
    ("channel_destinations", "created_at"):
        "UPDATE channel_destinations SET created_at = ? WHERE id = 'holdspeak-folder'",
    ("milestones", "achieved_at"):
        "UPDATE milestones SET achieved_at = ? WHERE key = 'timestamps.zoneless_to_utc.v1'",
}


def _python_value(table: str) -> str:
    if table == "channel_destinations":
        from holdspeak.db.channels import now_iso

        return now_iso()
    # holdspeak/db/zoneless_stamps.py writes the milestone this way.
    return datetime.now(timezone.utc).isoformat()


def restamp(conn: sqlite3.Connection) -> None:
    """Make each per-database random and time value again, as a fresh create does."""
    for (table, _column), sql in RESTAMPED.items():
        params = (_python_value(table),) if "?" in sql else ()
        conn.execute(sql, params)


_STATE: dict[str, Any] = {"installed": False, "off": False, "dir": None, "template": None, "real": None}


def enabled() -> bool:
    return os.environ.get("HOLDSPEAK_TEST_TEMPLATE_DB", "1") != "0"


def set_real_schema(on: bool) -> None:
    """The current test asked for the real schema path (``real_schema`` marker)."""
    _STATE["off"] = bool(on)


def real_ensure_schema() -> Callable[[Any], None]:
    return _STATE["real"]


def build_template(directory: Path) -> Path:
    """Build a self-contained template by the real path: no sidecars, WAL folded in."""
    from holdspeak.db.core import Database

    path = directory / "template.db"
    previous = _STATE["off"]
    _STATE["off"] = True  # the real schema path, never a copy
    try:
        db = Database(path)
    finally:
        _STATE["off"] = previous
    with db._connection() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.close()
    for suffix in ("-wal", "-shm", "-journal"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    return path


def _template() -> Path:
    if _STATE["template"] is None:
        directory = Path(tempfile.mkdtemp(prefix="hs-schema-template-"))
        _STATE["dir"] = directory
        _STATE["template"] = build_template(directory)
    return _STATE["template"]


def _copyable(db_path: Any) -> Optional[Path]:
    """The path when a copy may stand in for a fresh create, else None."""
    if not isinstance(db_path, (str, os.PathLike)):
        return None
    text = os.fspath(db_path)
    if not text or text == ":memory:" or text.startswith("file:"):
        return None
    path = Path(text)
    if path.exists() or not path.parent.is_dir():
        return None
    if any(Path(f"{path}{suffix}").exists() for suffix in ("-wal", "-shm", "-journal")):
        return None
    return path


def install() -> None:
    """Patch ``Database._ensure_schema`` for this process (idempotent).

    Called before the first test's fixtures, so the template is built before
    any test can patch the schema code, the clock or the environment.
    """
    if _STATE["installed"] or not enabled():
        return
    from holdspeak.db.core import Database

    real = Database._ensure_schema
    _STATE["real"] = real

    def _ensure_schema(self) -> None:
        path = None if _STATE["off"] else _copyable(self.db_path)
        if path is None:
            return real(self)
        template = _template()
        try:
            with open(template, "rb") as src, open(path, "xb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
        except FileExistsError:
            return real(self)
        with self._connection() as conn:
            restamp(conn)

    _ensure_schema._holdspeak_template = True  # type: ignore[attr-defined]
    Database._ensure_schema = _ensure_schema
    _STATE["installed"] = True
    _template()


def cleanup() -> None:
    directory = _STATE.get("dir")
    if directory is not None:
        shutil.rmtree(directory, ignore_errors=True)
