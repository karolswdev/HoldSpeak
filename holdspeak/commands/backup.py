"""Backup and restore subcommands for HoldSpeak.

The whole database lives in one SQLite file. `holdspeak backup` snapshots it to a
timestamped sibling on demand, so a user can take a copy before they upgrade.
`holdspeak restore` puts a backup back, snapshotting the current database first
so a restore can never be the step that loses data. The same `backup_database`
primitive runs automatically before any destructive schema action (HS-50-02).
"""

from __future__ import annotations

from pathlib import Path

from ..db.core import DEFAULT_DB_PATH, backup_database, restore_database


def _list_backups(db_path: Path) -> list[Path]:
    """Backups taken next to the database, newest name first."""
    return sorted(
        db_path.parent.glob(f"{db_path.name}.*.bak"), reverse=True
    )


def run_backup_command(args) -> int:
    """Handle `holdspeak backup`. Returns a process exit code."""
    db_path = DEFAULT_DB_PATH.expanduser()

    if not db_path.exists():
        print(f"No database to back up yet at {db_path}.")
        print("Run HoldSpeak once to create it, then back it up.")
        return 0

    backup = backup_database(db_path)
    print(f"Backed up {db_path}")
    print(f"      to {backup}")
    print("Keep this file to restore later with: holdspeak restore <file>")
    return 0


def run_restore_command(args) -> int:
    """Handle `holdspeak restore [backup] [--yes]`. Returns a process exit code."""
    db_path = DEFAULT_DB_PATH.expanduser()
    target = getattr(args, "backup", None)

    if not target:
        backups = _list_backups(db_path)
        if not backups:
            print(f"No backups found next to {db_path}.")
            print("Take one first with: holdspeak backup")
            return 0
        print("Available backups (newest first):")
        for path in backups:
            print(f"  {path}")
        print("\nRestore one with: holdspeak restore <file>")
        return 0

    backup_path = Path(target).expanduser()

    if db_path.exists() and not getattr(args, "yes", False):
        print(f"This will replace the current database at {db_path}")
        print(f"with {backup_path}.")
        answer = input("The current database is backed up first. Continue? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Restore cancelled. Nothing changed.")
            return 1

    try:
        safety = restore_database(backup_path, db_path)
    except ValueError as exc:
        print(f"Restore failed: {exc}")
        return 1

    print(f"Restored {db_path}")
    print(f"    from {backup_path}")
    if safety is not None:
        print(f"The previous database was saved to {safety}.")
    return 0
