"""The schema template (tests/_template_db.py) makes the database a fresh create makes.

Each test database is a copy of one template per test process. These guards
keep the copy honest: the same schema as a fresh create (so a schema change
cannot desync it), and each per-database random or time value made again.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.db.core import Database
from tests import _template_db

pytestmark = [
    pytest.mark.real_schema,
    pytest.mark.skipif(not _template_db.enabled(), reason="HOLDSPEAK_TEST_TEMPLATE_DB=0"),
]


def _seed_clock(monkeypatch):
    """Run the real schema/restamp under distinct SQL and Python instants."""
    from holdspeak.db import connection, channels, zoneless_stamps

    clock = [datetime(2030, 1, 1, tzinfo=timezone.utc)]
    real_apply = connection._apply_pragmas

    def apply(conn):
        real_apply(conn)
        # Delegate modifiers and non-now dates to SQLite itself.
        def sql_datetime(*args):
            values = tuple(clock[0].isoformat() if value == "now" else value for value in args)
            delegate = sqlite3.connect(":memory:")
            try:
                return delegate.execute("SELECT datetime(" + ",".join("?" for _ in values) + ")", values).fetchone()[0]
            finally:
                delegate.close()
        conn.create_function("datetime", -1, sql_datetime)
        conn.create_function("current_timestamp", 0, lambda: sql_datetime("now"))

    class SeedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock[0].astimezone(tz)

    monkeypatch.setattr(connection, "_apply_pragmas", apply)
    monkeypatch.setattr(channels, "datetime", SeedDateTime)
    monkeypatch.setattr(zoneless_stamps, "datetime", SeedDateTime)
    monkeypatch.setattr(_template_db, "datetime", SeedDateTime)
    return clock


def _fresh(path: Path) -> Path:
    Database(path).close()  # real_schema: the real script and reconcile
    return path


def _copy(path: Path) -> Path:
    _template_db.set_real_schema(False)
    try:
        Database(path).close()
    finally:
        _template_db.set_real_schema(True)
    return path


def _schema(path: Path) -> list[tuple]:
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        pragmas = [conn.execute(f"PRAGMA {name}").fetchone()[0] for name in ("user_version", "page_size", "journal_mode")]
    return rows + [("pragma", *pragmas)]


def _values(path: Path) -> dict[tuple[str, str], list]:
    """Every column of every table, as (table, column) -> its values in rowid order."""
    out: dict[tuple[str, str], list] = {}
    with sqlite3.connect(path) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for table in tables:
            columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
            rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            for index, column in enumerate(columns):
                out[(table, column)] = sorted((repr(row[index]) for row in rows))
    return out


def test_the_seam_is_installed() -> None:
    assert getattr(Database._ensure_schema, "_holdspeak_template", False)
    assert _template_db._STATE["template"] is not None


def test_a_copy_has_the_schema_of_a_fresh_create(tmp_path: Path) -> None:
    fresh = _fresh(tmp_path / "fresh.db")
    copy = _copy(tmp_path / "copy.db")
    assert _schema(copy) == _schema(fresh)


def test_a_copy_matches_a_fresh_create_except_the_restamped_values(tmp_path: Path) -> None:
    fresh = _values(_fresh(tmp_path / "fresh.db"))
    copy = _values(_copy(tmp_path / "copy.db"))
    assert fresh.keys() == copy.keys()
    differ = {key for key in fresh if fresh[key] != copy[key]}
    assert differ <= set(_template_db.RESTAMPED), differ - set(_template_db.RESTAMPED)


def test_restamped_names_every_value_a_fresh_create_makes_new(tmp_path: Path, monkeypatch) -> None:
    """Two fresh creates a second apart differ in exactly the RESTAMPED values.

    A new random, unique or time-stamped seed row in SCHEMA_SQL or reconcile
    fails here until it is added to RESTAMPED.
    """
    clock = _seed_clock(monkeypatch)
    first = _values(_fresh(tmp_path / "first.db"))
    clock[0] += timedelta(seconds=2)
    second = _values(_fresh(tmp_path / "second.db"))
    differ = {key for key in first if first[key] != second[key]}
    assert differ == set(_template_db.RESTAMPED)


def test_each_copy_gets_new_random_and_time_values(tmp_path: Path, monkeypatch) -> None:
    template = _values(_template_db._STATE["template"])
    _seed_clock(monkeypatch)
    one = _values(_copy(tmp_path / "one.db"))
    two = _values(_copy(tmp_path / "two.db"))
    for key in _template_db.RESTAMPED:
        assert one[key] != template[key], key
    hub_id = ("refinement_workspace_identity", "hub_id")
    assert one[hub_id] != two[hub_id]


def test_a_copy_never_writes_over_an_existing_database(tmp_path: Path) -> None:
    path = tmp_path / "kept.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE owner_rows (v TEXT)")
        conn.execute("INSERT INTO owner_rows VALUES ('kept')")
    _copy(path)  # the file exists: the real reconcile runs on it
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT v FROM owner_rows").fetchall() == [("kept",)]
        assert conn.execute("SELECT count(*) FROM refinement_workspace_identity").fetchone()[0] == 1
