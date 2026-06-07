# Phase 50 — Release Readiness ("cut a real 0.x") — Final Summary

**Status:** CLOSED (7/7). Opened and closed 2026-06-07.
**Branch:** `phase-50/story-01-version-ssot`. **PR:** to `main`, merged on green CI.

## Why this phase

HoldSpeak had shipped 49 phases of deep features and had never been cut as a real
release. It was a brilliant prototype with no front door. The user put it plainly
after Phase 49: "need this product to finally not suck", and picked
release-readiness over more features.

The grounded gaps that blocked a real release:

- The version was two different numbers (`pyproject.toml` 0.2.1 vs
  `holdspeak/__init__.py` 0.1.0), with no source of truth.
- `_ensure_schema` rebuilt the schema with no backup and no newer-than-known
  guard, so a future schema bump or a newer database opened by an older build was
  unguarded.
- There was no whole-database backup anywhere.
- `doctor` never looked at the database it depends on, and `Config` silently
  dropped unknown keys with no `config_version`.
- The install pinned git HEAD, not a tag, and had never been verified as a release
  artifact.

This phase made HoldSpeak safe to install, upgrade, and trust, without changing
meeting capture, dictation, plugins, synthesis, or routing.

## What shipped

- **HS-50-01 — One true version.** `holdspeak/__init__.py` resolves `__version__`
  from package metadata (`importlib.metadata`) with a `pyproject.toml` regex
  fallback, so `pyproject.toml` is the single source and the 0.1.0/0.2.1 split is
  gone. The version is surfaced in the `doctor` runtime line and in the
  `/api/setup/status` payload. `scripts/install.sh` pins a release tag via
  `HOLDSPEAK_REF` (default `v0.2.1`, `main` dev fallback).
  `tests/unit/test_version_ssot.py` pins code-version == pyproject-version.

- **HS-50-02 — Safe-by-default schema policy (the heart).** `_ensure_schema` now
  implements an explicit four-way matrix: create-fresh, no-op-equal,
  backup-then-apply-older, refuse-newer. `backup_database` snapshots the database
  before any destructive action; `SchemaVersionError` refuses a newer-than-known
  database and leaves it byte-for-byte untouched. One honest correction to the
  scaffold framing: the live `SCHEMA_SQL` is fully additive today (all
  `CREATE TABLE IF NOT EXISTS`, no `DROP`/`DELETE`), so there was no literal table
  wipe to fix. The real unguarded holes closed are a newer database silently run
  by an older build, and the absence of a backup before any future migration. This
  defines the forward upgrade contract. `tests/unit/test_db_schema_policy.py`
  covers all four cells.

- **HS-50-03 — Backup + restore.** `backup_database` upgraded to a consistent
  SQLite snapshot (`Connection.backup`); `restore_database` validates a backup,
  snapshots the current database first, then restores. `holdspeak backup` and
  `holdspeak restore` (list / restore with confirm + `--yes`) added to the CLI. A
  restore can never be the step that loses data.

- **HS-50-04 — doctor + config honesty.** A read-only Database check in `doctor`
  (current=PASS, older=WARN, newer=FAIL, unreadable=WARN) via a new
  `read_schema_version` probe that never triggers the refusal; it flows into
  `/api/setup/status` too. `Config` carries a `config_version` that coerces an
  older/unversioned shape forward without dropping fields and keeps + flags a newer
  one. Honest over silent in both places.

- **HS-50-05 — Verified clean-machine install.** Ran the documented
  `uv pip install -e .` in a fresh venv with a clean temp HOME; `holdspeak doctor`
  reaches exit 0 with only the expected optional warnings, and the version resolves
  to 0.2.1 from real install metadata. `install.sh` pins a tag via `HOLDSPEAK_REF`,
  verified statically. Transcript in `install-transcript.txt`. No breakage found.

- **HS-50-06 — Docs.** `docs/RELEASING.md` states the version/upgrade/backup
  policy (the four-way matrix in plain words, the config rule, `holdspeak backup` /
  `restore`, what `doctor` reports) plus a maintainer release checklist. README
  gained an "Upgrading and your data" subsection; GETTING_STARTED gained a backup
  pointer. Humanizer voice, doc guards green, every claim grounded in code.

- **HS-50-07 — Closeout.** This summary; the dogfood; the PR.

## The dogfood

`dogfood-transcript.txt` proves the safety matrix end to end with no real mic or
LLM (it drives the DB layer directly and simulates a version bump in-process):

- One true version: `__version__` == `pyproject` version.
- Fresh / empty database created at the current version; `doctor` reports it PASS.
- Same version: no-op, no backup taken.
- Older database: a backup is taken, the schema is applied, and the seeded data is
  intact in both the live DB and the backup; `doctor` PASS after.
- Newer database: refused with `SchemaVersionError`, the file is byte-for-byte
  untouched; `doctor` reports FAIL.
- Config: a newer config is kept and still loads its data (not silently reset).

Result line: `RESULT: PASS - HoldSpeak is safe to install, upgrade, and trust.`

## Verification

- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` -> 2451 passed,
  17 skipped.
- `cd web && npm run build` -> Complete; 0 `holdspeak/static/_built/` tracked.
- Clean-machine install -> `holdspeak doctor` exit 0 (HS-50-05 transcript).
- Dogfood -> PASS (`dogfood-transcript.txt`).

## Invariants held

- Never destroy data on upgrade: backup before any destructive action; a newer DB
  is refused, not rebuilt.
- The fresh-install path is unchanged: an empty/absent DB is still created at the
  current version with zero friction.
- Honest over silent: `doctor` and config report unexpected state plainly.
- Behavior-preserving: capture, dictation, plugins, synthesis, and routing are
  untouched; the temp-DB / `reset_database()` test idiom still works.

## Deferred / maintainer steps

- **PyPI publish.** This phase readies the gate; the publish itself is a deliberate
  maintainer step once the gate is green, per `docs/RELEASING.md`. Not done here.
- **Pushing the `v0.2.1` tag.** `install.sh` pins it by default; the tag is pushed
  at release time (release checklist step 7). Until then, `HOLDSPEAK_REF=main` is
  the working dev ref.

## Follow the cadence

Project README, phase `current-phase-status.md`, BACKLOG candidate C, and the
story headers are all updated to CLOSED / shipped in this closeout.
