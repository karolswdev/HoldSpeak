# Evidence — HS-50-04: doctor + config honesty

Write-once record of making `doctor` tell the truth about the database it depends
on, and giving `Config` a version so an evolving format does not fail invisibly.
The rule that matters: report unexpected state plainly, never silently fix
something in a way that hides a problem.

## What shipped

**A database check in doctor** (`holdspeak/commands/doctor.py` `_check_database`)
- Reports the stored schema version against this build, read-only via the new
  `read_schema_version` probe so it never triggers HS-50-02's refusal:
  - absent file -> PASS, "created on first use" (normal before first run).
  - current version -> PASS, "Schema version N (current)".
  - older -> WARN, "older than this build ... backs the database up and upgrades
    it on the next start", fix points at `holdspeak backup`.
  - newer -> FAIL, "newer than this build; this build refuses to open it", fix
    points at upgrading or `holdspeak restore`.
  - present-but-unreadable -> WARN.
- Wired into `collect_doctor_checks` right after the config check, so it flows
  into both `holdspeak doctor` and `/api/setup/status` (which composes its
  sections from the same checks).

**A read-only schema probe** (`holdspeak/db/core.py` `read_schema_version`)
- Module-level function returning the stored version (or None) without opening
  the DB for use or creating the file. `Database._read_schema_version` now
  delegates to it. Catches `sqlite3.DatabaseError` (the parent of
  `OperationalError`) so a file that is not a SQLite database at all reads as
  "no version" rather than raising. Exported from `holdspeak.db` alongside
  `restore_database`.

**Config gets a version** (`holdspeak/config.py`)
- `CONFIG_VERSION = 1` and a `config_version: int` field on `Config` (defaults to
  the current version, so `save()` round-trips it).
- `_coerce_config_version()` in `load()`: a missing or non-int version (a
  pre-versioning config) and an older version both coerce forward to the current
  version without dropping any known field; a newer version is kept as-is and
  logged at WARNING, so the user is not locked out but the state is visible.
- `_check_config` in doctor now flags a config newer than this build (WARN) and
  shows the config version on the PASS line.

## Honest, not silent

- A newer database is a hard FAIL in doctor and a hard refusal at open time
  (HS-50-02): the same truth in both places, by design (the story asked for this).
- A newer config is loaded (no lockout) but flagged in logs and in doctor; it is
  not silently coerced down.
- The forward coercion of an older/unversioned config is a no-op today (no fields
  have changed yet); it is the hook a real future migration would use, and it
  keeps every existing key.

## Tests (`tests/unit/test_doctor_config_honesty.py`)

- Database check: absent -> PASS, current -> PASS, newer-stamped -> FAIL,
  non-database file -> WARN.
- Config: default carries the current version; save/load round-trips it; a
  version-less config with a retired key coerces forward and keeps `hotkey.key`;
  a newer-version config is preserved, still loads its data, and warns; doctor's
  config check flags a newer config.

```
uv run pytest -q tests/unit/test_doctor_config_honesty.py
-> 9 passed

uv run pytest -q -k "doctor or config or setup_status" --ignore=tests/e2e/test_metal.py
-> 163 passed, 2 skipped

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2451 passed, 17 skipped   (was 2442; +9 from this story)
```

No UI bundle touched; 0 `_built/` tracked.

## Not done here (by design)

- The schema policy (HS-50-02) and the backup/restore surface (HS-50-03) are the
  mechanisms this story reports on; it adds the honest reporting + config
  versioning only.
