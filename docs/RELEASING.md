# Releasing, upgrading, and your data

This page describes version records, additive database repair, backups, release
checks, and data boundaries. For first installation, read
[Getting Started](GETTING_STARTED.md).

## Versions

- `pyproject.toml` owns the package version. `holdspeak.__version__` reads it.
- `SCHEMA_VERSION` in `holdspeak/db/schema.py` is an informational database
  stamp.
- `CONFIG_VERSION` owns the config stamp.

Do not edit a version stamp in a user's database or config by hand.

## What happens to your data on upgrade

HoldSpeak has additive schema reconciliation, not an ordered migration ladder.
On open it adds missing structures, repairs named legacy tables, refreshes
triggers, and runs named data repairs. General repair keeps unknown tables and
rows. A newer schema stamp does not guarantee that a downgrade works.

An automatic backup can happen after repair. It is not the original pre-repair
file. Run [Storage and migrations](STORAGE_AND_MIGRATIONS.md) before an upgrade
when that copy matters.

The People sidecar and key are outside the main database backup. Browser storage,
capture journals, config, and connector credentials also need their own
handling.

## Back up before you upgrade

```console
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
```

Restore saves the current database first and refuses while another process has
the file open. Practice on a copy. Do not treat a successful file replacement
as proof that external providers or People keys are available.

## Run the checks

Use an isolated home for automated checks. HoldSpeak resolves its database and
config from the process home.

Critical journeys:

```console
HOME=$(mktemp -d) uv run pytest -q -m critical tests/critical -p no:cacheprovider
```

Web contract:

```console
npm --prefix web run check
```

The full suite and hardware lane are release checks, not evidence that a
particular model route is useful. The hardware lane needs a microphone,
permissions, model files, and a real keyboard. Never run it against a user's
real Desk without explicit isolation.

### Evaluate a model route

Use the evaluation harness for a configured model endpoint:

```console
uv run python scripts/phase200_eval.py run \
  --endpoint http://<host>:8080/v1 \
  --model <model-name> \
  --report .tmp/phase200-eval.json \
  --raw .tmp/phase200-eval-raw.json
```

The harness uses temporary homes and databases. A passing run measures the
synthetic episodes only. Inspect critical factual failures and aborted episodes.

## Cut a release

1. Set the package version in `pyproject.toml`.
2. Confirm `holdspeak.__version__` returns it.
3. Raise schema or config stamps only when their shapes changed.
4. Run the critical, Web, full, and relevant hardware checks.
5. Test a clean install and run `holdspeak doctor`.
6. Update the default `HOLDSPEAK_REF` in `scripts/install.sh`.
7. Tag the release and push the tag.

The release workflow builds the Web bundle, sdist, and wheel, checks that the
wheel has `static/_built/`, and publishes with trusted publishing. A tag push
publishes. Check the workflow result and package contents.

## Related

- [Getting Started](GETTING_STARTED.md)
- [Operations](OPERATIONS.md)
- [Models](MODELS.md)
- [Storage and migrations](STORAGE_AND_MIGRATIONS.md)
- [README](../README.md)
