# Releasing, upgrading, and your data

This page explains how HoldSpeak versions itself, what happens to your data
when you upgrade, and how to cut a release. For a first install, read
[Getting Started](GETTING_STARTED.md).

## Versions

- The package version in `pyproject.toml` (`project.version`) is the single
  source. `holdspeak.__version__` reads it from the installed package.
  `holdspeak doctor` shows it on the Runtime line.
- The database has a `SCHEMA_VERSION` in `holdspeak/db/schema.py`. HoldSpeak
  writes it on every open. It is informational. Nothing refuses to open
  because of it.
- The config file `~/.config/holdspeak/config.json` has a `config_version`.
  The constant is `CONFIG_VERSION` in `holdspeak/config/core.py`.

You do not manage these values by hand.

## What happens to your data on upgrade

HoldSpeak has no ordered migration ladder. At start it compares the database
with the schema of the build and repairs the difference. It adds missing
tables and columns. It also runs a few table rebuilds and data repairs.

- **No database.** HoldSpeak creates the declared schema.
- **Existing database.** HoldSpeak repairs the shape. General repair adds
  missing structures. Named legacy repairs rebuild tables and replace schema
  objects.
- **Newer schema stamp.** HoldSpeak still opens the file. A downgrade is not
  guaranteed to work. Inspect the schema before you rely on one.
- **Config.** An older config loads forward and keeps your settings. A newer
  config still loads. The log and `holdspeak doctor` flag it, because some
  settings may be ignored.

An automatic backup can happen after some schema changes. It is not a copy of
the file as it was before the upgrade. For that copy, make your own backup.
See [Storage and migrations](STORAGE_AND_MIGRATIONS.md) for the exact order.

## Back up before you upgrade

```console
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
```

Use [Operations](OPERATIONS.md) for the full backup and restore steps, the
limits of a backup, and the checks of a running hub. The short rules:

- A backup covers the main database only. The People store and the keychain
  credentials are outside it.
- Restore saves your current database first.
- Restore refuses while another process has the database open.
- Practice a restore on a copy before you restore for real.

## Run the checks

Always use an isolated home. HoldSpeak resolves its database and config from
your home directory when it imports. A test run under your real home writes to
your real data. The test suite refuses to start against a real installation.
A live, attended walk sets `HOLDSPEAK_ALLOW_REAL_HOME=<walk name>` to opt in.

**Critical journeys.** Four journeys use the real services and replace only
the outside adapters: identity, backup and restore, a first sentence with no
model, and a Project first result. They need no model, microphone or network.

```sh
HOME=$(mktemp -d) uv run pytest -q -m critical tests/critical -p no:cacheprovider
```

CI runs them as the job `Critical Journeys (G0)`.

**Full suite.**

```sh
HOME_REAL=$HOME; HOME=$(mktemp -d) \
  PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright \
  npm_config_cache=$HOME_REAL/.npm \
  uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py
```

**Web contract.**

```sh
npm --prefix web run check
```

**Hardware lane.** `-m metal --run-metal` needs a real microphone, model and
keyboard. CI never runs it.

A test skips when its dependency is missing, and it states the reason. A skip
describes the machine. It is not a pass.

### Evaluate a model route

A passing test does not show that a model is good enough for real work. The
evaluation harness runs 33 synthetic episodes through the real product path
with one selected route. The episodes cover the Interview, meeting extraction
and grounded updates.

```sh
uv run python scripts/phase200_eval.py run \
    --endpoint http://<host>:8080/v1 \
    --model <model-name> \
    --report .tmp/phase200-eval.json --raw .tmp/phase200-eval-raw.json
```

The command exits with 0 when no episode has a critical factual failure. It
exits with 1 when one has, or when the run aborts. A critical failure is an invented value, a broken
correction, a restated old decision, or an irrelevant citation. A person must
inspect the source of each one.

The run uses a temporary home and a temporary database for each episode. It
never reads your data. The report has an `aborted` column. Read the reason in
it before you read any count. See the
[scoring protocol](internal/architect-assistant/proof/SCORING.md) for the
fields and the reviewer rubric.

## Cut a release

1. Set the new version in `pyproject.toml`.
2. Run `python -c "import holdspeak; print(holdspeak.__version__)"`. It must
   print the new version. `tests/unit/test_version_ssot.py` checks this.
3. If the database or config shape changed, raise `SCHEMA_VERSION` or
   `CONFIG_VERSION`. Most releases change neither.
4. Run the critical journeys, the full suite and the web contract. Read the
   output.
5. Check a clean install. Create a fresh virtual environment, run
   `uv pip install -e .`, then run `holdspeak doctor`. It must exit with 0.
   Optional gaps, such as a missing local model, are acceptable.
6. Set the default `HOLDSPEAK_REF` in `scripts/install.sh` to the new tag.
7. Tag the release (`vX.Y.Z`) and push the tag.

The tag push is the publish. It runs `.github/workflows/release.yml`. The
workflow builds the web bundle, builds the sdist and the wheel, and checks
that the wheel holds `static/_built/`. Then it publishes to PyPI with trusted
publishing. Push the tag only when the checks pass.

You can also start the workflow by hand. It then publishes the current head of
the default branch.

## Related

- [Getting Started](GETTING_STARTED.md)
- [Operations](OPERATIONS.md)
- [Models](MODELS.md)
- [README](../README.md)
