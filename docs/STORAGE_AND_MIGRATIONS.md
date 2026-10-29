# Storage and migrations

HoldSpeak keeps ordinary Desk records in a SQLite database. People uses a
separate encrypted sidecar. This page describes the stores, additive
reconciliation, backup, restore, and restart recovery.

## Back up before you upgrade

Use the CLI before a schema or package upgrade:

```console
holdspeak backup
holdspeak restore
holdspeak restore <backup-file>
```

Restore lists backups when no file is supplied. It saves the current database
before replacement, refuses while the hub has the database open, and removes
the old WAL and shared-memory files. The final copy is not an atomic rename.
Stop the hub and do not interrupt restore.

The database backup does not include config, browser storage, capture files, or
the People sidecar and its key. See [Security](SECURITY.md).

## Where the data is

The default database is
`~/.local/share/holdspeak/holdspeak.db`
(`DEFAULT_DB_PATH` in `holdspeak/db/core.py`). Connections enable foreign
keys, WAL journaling, and a five-second busy timeout. A clean context commits;
an exception rolls back.

| Class | Examples | Role |
| --- | --- | --- |
| Domain records | `meetings`, `segments`, `projects`, `decisions`, `artifacts` | Sources and saved work |
| Queues and ledgers | `intel_jobs`, `activity_records`, `kernel_journal` | Work, attempts, and evidence |
| Kernel authority | `kernel_operations`, `kernel_receipts`, `kernel_parent_runs`, grants | Admission and restart state |
| Derived views | `segments_fts`, `memory_chunks_fts`, projection stages | Search and recovery |
| Schema machinery | `schema_version`, indexes, triggers | SQLite shape |

Capture checkpoints live in the meeting capture journal. People records live
in `people.v1.sqlite3` and are encrypted before persistence.

## How the schema repairs itself

`SCHEMA_SQL` in `holdspeak/db/schema.py` declares the current shape.
`SCHEMA_VERSION` is informational. A newer or older stamp does not by itself
block startup.

On open, `reconcile_schema` in `holdspeak/db/reconcile.py`:

1. rebuilds named legacy tables that cannot be repaired with `ALTER TABLE`;
2. adds missing columns;
3. creates missing tables, indexes, and triggers;
4. replaces changed triggers;
5. runs independent data repair passes and stamps the result.

General repair preserves unknown tables and rows. It does not drop columns.
Named table rebuilds and trigger replacement can replace an object by design.
There is no ordered rollback ladder.

For a missing bookmarks table, the table is recreated before the automatic backup is called.
The automatic backup is therefore not a copy of the original pre-repair file.
Run `holdspeak backup` first when you need that original shape.

## Rules the schema enforces

- Meeting children use their declared cascade or source-state behavior.
- Transcript search triggers keep `segments_fts` aligned with `segments`.
- Decisions retain source identity and can be marked `source_deleted`.
- Inference attestations have no-update and no-delete triggers.
- Kernel receipts, journal events, and checkpoints are evidence, not a process view.

## Objects and derived views

`kernel_parent_runs.input_json` stores caller input snapshots.
The kernel filter rejects named audio, PCM, and token fields. It does not reject
every prompt or transcript string.

`segments_fts` is rebuilt from `segments`; editing it does not edit a
transcript. A projection stage becomes `PUBLISHED` only through its materializer
after a terminal receipt.

## Startup and recovery

Database shape repair completes before services use the file. The kernel then:

1. opens the journal store;
2. reconciles abandoned parent runs;
3. recovers inference route executions;
4. reaps expired claims;
5. recovers projection stages.

A restart can turn unfinished work into `refused` or `indeterminate`. It does
not turn a missing receipt into success.

## See also

- [Operations](OPERATIONS.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Data model](DATA_MODEL.md)
- [Security model](SECURITY_MODEL.md)
