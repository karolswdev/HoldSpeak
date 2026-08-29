# Releasing, upgrading, and your data

This is the contract for how HoldSpeak versions itself, what happens to your
data when you upgrade, and how to be safe about it. HoldSpeak no longer carries
an ordered historical migration ladder. Every supported database is reconciled
against the canonical shape instead.

If you are installing for the first time, start with
[`GETTING_STARTED.md`](GETTING_STARTED.md) instead.

## Versions, and where they live

HoldSpeak has one version, and one source of truth for it.

- The package version in `pyproject.toml` is that source. `holdspeak.__version__`
  reads it from the installed package metadata, so the running code and the
  package always agree. `holdspeak doctor` prints it on the Runtime line.
- The database carries a `SCHEMA_VERSION`. It is stamped into the database file
  on every open as an informational record; nothing gates on it.
- The config file (`~/.config/holdspeak/config.json`) carries a `config_version`.

You do not manage any of these by hand. They exist so HoldSpeak can tell whether
the data it found was written by this build, an older one, or a newer one, and
act safely on the answer.

## What happens to your database on upgrade

When HoldSpeak starts, it reconciles the database to the canonical schema shape
defined in the build. The reconcile is declarative: it creates any missing
tables, indexes, and triggers, adds any missing columns, and runs idempotent
data backfills only when the shape actually changed. It is additive-only (it
never drops a table, drops a column, or deletes a row).

- **No database yet.** A fresh database is created at the current schema. This
  is the normal first-run path.
- **Existing database, same shape.** Nothing happens. This is the common case
  on every start.
- **Existing database, missing tables or columns.** HoldSpeak backs the
  database up first (a timestamped copy next to your database, logged), then
  adds what is missing and runs the backfills. No upgrade changes your data
  without leaving a recoverable copy first.
- **Database stamped newer than this build.** HoldSpeak opens it without
  error. The reconcile adds anything the live file is missing and moves on;
  it never removes anything a newer build wrote.

The same logic governs the config file. An older or unversioned config is read
forward without dropping your settings. A config newer than this build is still
loaded so you are not locked out, but it is flagged (in the log and in `doctor`)
because some of its settings may not be understood.

## Back up before you upgrade

Your whole HoldSpeak database is a single SQLite file. You can copy it at any
time with one command:

```bash
holdspeak backup
```

This writes a timestamped snapshot next to your database and prints the path.
The automatic backup on a shape-changing reconcile uses the same mechanism, so
even if you forget, an upgrade still protects you. Taking your own copy first is
the belt-and-suspenders move before a version jump.

To see your backups, or to put one back:

```bash
holdspeak restore               # list the backups next to your database
holdspeak restore <backup-file> # restore that backup
```

Restore snapshots your current database before it overwrites it, so a restore can
never be the step that loses data. If you restore the wrong file, the state you
were in is still saved.

## What doctor tells you

`holdspeak doctor` reports the state it actually found, so you are never guessing:

- **Database.** The check reports the path, informational schema stamp, and
  table count. A missing database is a clean first-run state. A file that is
  not readable SQLite, or has no HoldSpeak tables, reads as a warning.
- **Config.** A config newer than this build reads as a warning that some settings
  may be ignored. Otherwise it passes and shows the config version.

Run `doctor` after an upgrade if you want confirmation that everything lines up.

## Maintainer release checklist

For whoever cuts a release:

1. Decide the new version and set it in `pyproject.toml` (`project.version`). This
   is the only place the number lives.
2. Confirm the code agrees: `python -c "import holdspeak; print(holdspeak.__version__)"`
   prints the new number. The drift test (`tests/unit/test_version_ssot.py`)
   enforces this, so step 4 also covers it.
3. If the on-disk database or config shape changed, bump `SCHEMA_VERSION`
   (`holdspeak/db/schema.py`) or `CONFIG_VERSION`
   (`holdspeak/config/core.py`). The
   schema reconcile handles forward changes automatically (additive-only); the
   version bump is an informational stamp. Most releases change neither.
4. Run the suite and read the output:
   `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
5. Verify the clean install: a fresh virtual environment, `uv pip install -e .`,
   then `holdspeak doctor` reaches exit 0 (optional gaps like a missing local
   model are fine). See the captured example in the release evidence.
6. Set the default install ref to the new tag: `HOLDSPEAK_REF` in
   `scripts/install.sh` (default) so a script install pins the release.
7. Tag the release (`vX.Y.Z`) and push the tag. **The tag is the publish**:
   pushing it runs the release workflow, which builds and publishes to PyPI
   via trusted publishing and creates the GitHub release. Only push the tag
   when the gate above is green.

## Related

- [`GETTING_STARTED.md`](GETTING_STARTED.md) for first-time install and run.
- [`../README.md`](../README.md) for the install surface and project status.
- [`MODELS.md`](MODELS.md) for the model contract.
