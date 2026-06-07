# HS-50-03 — Backup + restore

- **Project:** holdspeak
- **Phase:** 50
- **Status:** backlog
- **Depends on:** HS-50-02
- **Unblocks:** HS-50-07
- **Owner:** unassigned

## Problem
There is no whole-database backup anywhere. The only export today is per-meeting
(`meeting_exports.py`, `GET /api/meetings/{id}/export`). A safe upgrade (HS-50-02)
needs a backup primitive to call before any destructive action, and the user needs
a way to take a backup on demand before they upgrade.

## Scope
- **In:**
  - A backup primitive: copy the live SQLite DB to a timestamped sibling
    (file copy or `sqlite3` `.backup`), returning the backup path.
  - A `holdspeak backup` CLI command (and/or a guarded API) that runs it on demand.
  - HS-50-02 calls this automatically before any destructive schema action; the
    user is told where the backup is.
  - Restore at least documented ("copy this file back"); a real `holdspeak restore`
    is a plus if cheap.
- **Out:** the schema matrix (HS-50-02); doctor surfacing (HS-50-04). This story is
  the backup primitive + entry point.

## Acceptance criteria
- [ ] A backup primitive copies the live DB to a timestamped file and returns its
      path; it is invoked automatically before any destructive schema action.
- [ ] A `holdspeak backup` entry point exists and is documented.
- [ ] No data is lost: the backup is a faithful copy (open it, read a row).
- [ ] Tests assert a backup file is produced + readable; the auto-backup fires on
      the older-version upgrade path.

## Test plan
- Unit/integration: take a backup of a seeded DB -> the file exists, opens, and has
  the rows; the HS-50-02 older-version path produces a backup before applying.
  `uv run pytest -q -k "backup or schema or db"`.

## Notes / open questions
- Default backup location: a `backups/` sibling of the DB, or alongside it with a
  timestamp suffix. Keep it next to the DB so it is obvious and local.
- Prefer `sqlite3.Connection.backup()` over a raw file copy if the DB might be open
  (consistent snapshot).
