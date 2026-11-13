#!/usr/bin/env python3
"""Remove the dead Telegram poll records from a HoldSpeak database.

Until 2026-11-13 each Telegram long poll that timed out was one full egress
operation in the kernel journal. This tool removes those operations (state
indeterminate, refused or failed; connector reach-telegram; data class
reach_update_cursor) and nothing else. The journal keeps one signed
checkpoint for each run of removed records, so its hash chain still verifies
(holdspeak/kernel/journal_prune.py).

    uv run python scripts/prune_empty_polls.py                 # dry run: counts only
    uv run python scripts/prune_empty_polls.py --apply         # stop the hub first

The dry run reads counts and sizes; it prints no content. ``--apply`` refuses
while a hub owns the database, makes a backup with the sqlite backup API
first (the backup is parked, never deleted), removes the records in one
transaction, runs VACUUM, verifies the chain and prints the sizes.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_BACKUP = Path.home() / "HoldSpeak-parked-2026-11-13" / "holdspeak.before-poll-prune.db"
_TABLES = ("kernel_journal", "kernel_receipts", "kernel_operations")


def _mb(count: float) -> str:
    return f"{count / 1_048_576:.1f} MB"


def _file_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in (path, Path(f"{path}-wal")) if p.exists())


def _table_bytes(conn: sqlite3.Connection) -> dict[str, int]:
    """Bytes for each kernel table with its indexes; {} without dbstat."""
    try:
        rows = conn.execute(
            """SELECT m.tbl_name, SUM(s.pgsize) FROM dbstat s JOIN sqlite_master m ON m.name = s.name
                WHERE m.tbl_name IN (?,?,?) GROUP BY m.tbl_name""", _TABLES).fetchall()
    except sqlite3.DatabaseError:
        return {}
    return {str(name): int(size or 0) for name, size in rows}


def survey(db_path: Path) -> dict[str, object]:
    """Counts only: what a prune removes and what it leaves."""
    from holdspeak.kernel import journal_prune

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        dead = f"({journal_prune.DEAD_POLLS_SQL})"
        marks = (*journal_prune._DEAD_STATES, *journal_prune._POLL_REFS)
        tables = {}
        for table in _TABLES:
            total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            goes = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE operation_id IN {dead}", marks).fetchone()[0]
            tables[table] = {"rows": int(total), "removed": int(goes)}
        states = {str(state): int(count) for state, count in conn.execute(
            f"SELECT state, COUNT(*) FROM kernel_operations WHERE operation_id IN {dead} GROUP BY state", marks)}
        return {"tables": tables, "states": states, "bytes": _table_bytes(conn), "file": _file_bytes(db_path)}
    finally:
        conn.close()


def _print_survey(found: dict[str, object], *, word: str) -> None:
    tables, sizes = found["tables"], found["bytes"]
    print(f"Dead Telegram polls by state: {found['states'] or 'none'}")
    for table in _TABLES:
        row = tables[table]
        share = row["removed"] / row["rows"] if row["rows"] else 0
        size = f", about {_mb(sizes[table] * share)} of {_mb(sizes[table])}" if table in sizes else ""
        print(f"  {table}: {word} {row['removed']:,} of {row['rows']:,} rows{size}")
    print(f"Database file: {_mb(found['file'])}")


def hub_owner(db_path: Path) -> int | None:
    """The pid of a live hub that owns this database, else None."""
    from holdspeak import runtime_lock

    owner = runtime_lock.read_owner(db_path)
    pid = int((owner or {}).get("pid") or 0)
    return pid if pid and runtime_lock.pid_alive(pid) else None


def apply(db_path: Path, backup: Path) -> dict[str, object]:
    from holdspeak.db import Database
    from holdspeak.kernel.journal import JournalStore

    if backup.exists():
        raise SystemExit(f"A backup is at {backup} already. Move it, or name another with --backup.")
    backup.parent.mkdir(parents=True, exist_ok=True)
    before = _file_bytes(db_path)
    source, target = sqlite3.connect(str(db_path)), sqlite3.connect(str(backup))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    check = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
    try:
        if check.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise SystemExit("The backup did not pass its check. Nothing was removed.")
    finally:
        check.close()
    print(f"Backup: {backup} ({_mb(backup.stat().st_size)})")

    database = Database(db_path)
    store = JournalStore(database._connection)
    store.verify()
    counts = store.prune_operations(store.dead_poll_operation_ids())
    database.close()
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
    verified = JournalStore(Database(db_path)._connection).verify()
    return {"counts": counts, "verified": verified, "before": before, "after": _file_bytes(db_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--db", type=Path, default=None, help="the database (default: this user's HoldSpeak database)")
    parser.add_argument("--apply", action="store_true", help="remove the records (default: a dry run)")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help=f"backup file (default: {DEFAULT_BACKUP})")
    args = parser.parse_args(argv)
    db_path = args.db
    if db_path is None:
        from holdspeak.db.core import DEFAULT_DB_PATH

        db_path = DEFAULT_DB_PATH
    db_path = db_path.expanduser().resolve()
    if not db_path.exists():
        print(f"No database at {db_path}.")
        return 2
    print(f"Database: {db_path}")
    found = survey(db_path)
    if not args.apply:
        _print_survey(found, word="would remove")
        print("Dry run: nothing was changed. Stop the hub, then run again with --apply.")
        return 0
    pid = hub_owner(db_path)
    if pid is not None:
        print(f"A hub owns this database (process {pid}). Stop the hub, then run again.")
        return 3
    _print_survey(found, word="removes")
    done = apply(db_path, args.backup.expanduser())
    counts, verified = done["counts"], done["verified"]
    print(f"Removed: {counts['operations']:,} operations, {counts['journal_records']:,} journal records, "
          f"{counts['receipts']:,} receipts.")
    print(f"Chain verified: {verified['records']:,} records stay, {verified['pruned']:,} are behind checkpoints.")
    print(f"Database file: {_mb(done['before'])} before, {_mb(done['after'])} after.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
