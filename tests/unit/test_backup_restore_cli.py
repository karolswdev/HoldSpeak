"""The `holdspeak backup` / `holdspeak restore` CLI surface (HS-50-03).

Backup snapshots the live DB to a timestamped file the user can keep before an
upgrade. Restore puts a backup back, snapshotting the current DB first so a
restore can never be the step that loses data.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.commands import backup as backup_cmd
from holdspeak.db import Database, reset_database
from holdspeak.db.core import restore_database


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    reset_database()
    path = tmp_path / "holdspeak.db"
    # Point the CLI at this throwaway DB, never the developer's real one.
    monkeypatch.setattr(backup_cmd, "DEFAULT_DB_PATH", path)
    yield path
    reset_database()


def _seed(path: Path, title: str) -> None:
    Database(path)
    conn = sqlite3.connect(str(path))
    conn.execute(
        "INSERT OR REPLACE INTO meetings (id, title, started_at) VALUES ('m1', ?, datetime('now'))",
        (title,),
    )
    conn.commit()
    conn.close()


def _title(path: Path) -> str | None:
    conn = sqlite3.connect(str(path))
    try:
        row = conn.execute("SELECT title FROM meetings WHERE id = 'm1'").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def test_backup_produces_a_readable_copy(db_path: Path, capsys) -> None:
    _seed(db_path, "Original")
    rc = backup_cmd.run_backup_command(SimpleNamespace())
    assert rc == 0

    backups = list(db_path.parent.glob(f"{db_path.name}.*.bak"))
    assert len(backups) == 1
    assert _title(backups[0]) == "Original"
    assert str(backups[0]) in capsys.readouterr().out


def test_backup_with_no_database_is_a_clean_noop(db_path: Path, capsys) -> None:
    assert not db_path.exists()
    rc = backup_cmd.run_backup_command(SimpleNamespace())
    assert rc == 0
    assert "No database to back up" in capsys.readouterr().out
    assert list(db_path.parent.glob("*.bak")) == []


def test_restore_with_no_arg_lists_backups(db_path: Path, capsys) -> None:
    _seed(db_path, "Original")
    backup_cmd.run_backup_command(SimpleNamespace())
    capsys.readouterr()

    rc = backup_cmd.run_restore_command(SimpleNamespace(backup=None, yes=False))
    out = capsys.readouterr().out
    assert rc == 0
    assert "Available backups" in out
    assert ".bak" in out


def test_restore_brings_back_old_data_and_snapshots_current(db_path: Path, capsys) -> None:
    _seed(db_path, "Original")
    backup_cmd.run_backup_command(SimpleNamespace())
    backup_file = next(iter(db_path.parent.glob(f"{db_path.name}.*.bak")))
    capsys.readouterr()

    # Move on: the live DB now holds different data.
    _seed(db_path, "Changed")
    assert _title(db_path) == "Changed"

    rc = backup_cmd.run_restore_command(
        SimpleNamespace(backup=str(backup_file), yes=True)
    )
    assert rc == 0
    assert _title(db_path) == "Original"
    # The "Changed" state was snapshotted before being overwritten.
    out = capsys.readouterr().out
    assert "previous database was saved" in out


def test_restore_rejects_a_non_database_file(db_path: Path, tmp_path, capsys) -> None:
    _seed(db_path, "Original")
    junk = tmp_path / "notadb.bak"
    junk.write_text("this is not sqlite")

    rc = backup_cmd.run_restore_command(SimpleNamespace(backup=str(junk), yes=True))
    assert rc == 1
    assert "not a readable HoldSpeak database" in capsys.readouterr().out
    # The live DB is untouched.
    assert _title(db_path) == "Original"


def test_restore_database_primitive_returns_safety_backup(tmp_path) -> None:
    reset_database()
    live = tmp_path / "holdspeak.db"
    _seed(live, "Live")
    snapshot = tmp_path / "snap.bak"
    Database(snapshot)  # a valid empty HoldSpeak DB to restore from

    safety = restore_database(snapshot, live)
    assert safety is not None and safety.exists()
    reset_database()
