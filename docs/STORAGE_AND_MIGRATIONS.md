# Storage and migrations

HoldSpeak keeps its records in one SQLite file.
This page says where the file is, how the schema repairs itself, and how to back up and restore.
The [schema inventory](generated/schema-inventory.json) lists the declared tables.
It comes from `SCHEMA_SQL`.
It does not show the shape of an older database that has not been repaired yet.

## Back up before you upgrade

1. Run `holdspeak backup`.
2. Keep the file path that the command prints.

The file is a timestamped copy next to the database.
Run `holdspeak restore` with no argument to list the copies.
Run `holdspeak restore <backup-file>` to put one back.
Add `--yes` to skip the confirmation.

Restore refuses to run when `holdspeak web` is open or when the file is not writable.
Stop the hub first.
Restore takes a safety copy of the current database before it replaces the file.
It also removes the old `-wal` and `-shm` files.
The final file copy is not an atomic rename.
Do not stop a restore halfway.

Backup and restore cover the database only.
They do not cover config, audio files, browser storage, or People data.
[SECURITY.md](SECURITY.md) lists those stores.
[OPERATIONS.md](OPERATIONS.md) has the doctor and restart steps.

## Where the data is

The default path is `~/.local/share/holdspeak/holdspeak.db` (`DEFAULT_DB_PATH` in `holdspeak/db/core.py`).
You can pass another path to `Database`.
Each connection turns on foreign keys, WAL journaling, and a five-second busy timeout (`holdspeak/db/connection.py`).
A connection commits when its context exits and rolls back on an error.

| Class | Examples | Role |
| --- | --- | --- |
| Domain objects | `meetings`, `segments`, `action_items`, `projects`, `decisions`, `artifacts` | Your records and their sources |
| Queues and ledgers | `intel_jobs`, `intel_job_attempts`, `activity_records`, `kernel_journal` | Work descriptors, attempts, evidence |
| Kernel authority | `kernel_operations`, `kernel_receipts`, `kernel_parent_runs`, `kernel_parent_checkpoints`, grants | Admission, approval, restart state |
| Derived views | `segments_fts`, `memory_chunks_fts`, `kernel_projection_stages` | Search, display, recovery |
| Schema machinery | `schema_version`, indexes, triggers | A version stamp and SQLite upkeep |

## How the schema repairs itself

`SCHEMA_SQL` in `holdspeak/db/schema.py` declares the schema.
`SCHEMA_VERSION` is an informational stamp.
Nothing reads it to block a start.
A database with a newer or older stamp still opens.

On open, `reconcile_schema` (`holdspeak/db/reconcile.py`) compares the live file with the declared SQL.
It runs these steps:

1. Rebuild four legacy tables that `ALTER TABLE` cannot fix: the intelligence queue, parent runs, action items, and thread message parts.
2. Add missing columns to existing tables.
3. Run `SCHEMA_SQL` in one transaction to create missing tables, indexes, and triggers.
4. Replace triggers whose text changed, then run the independent repair passes.
5. If the shape changed on an existing file, back up the database, run the data backfills, and stamp the version.

The general repair keeps unknown tables and rows.
It does not drop columns.
The legacy rebuilds and the trigger refresh replace objects.

The automatic backup is not a snapshot of the original shape.
Schema changes and repair passes run before it.
For a missing bookmarks table, the table is recreated before the automatic backup is called.
Run `holdspeak backup` first when you need an original copy.

The code has no rollback chain.
It has additive repair and a few named data repairs.
A rename does not repair itself unless `reconcile.py` has a function for it.

## Rules the schema enforces

- Meeting children usually cascade when you delete the meeting.
- Triggers keep `segments_fts` current on insert, update, and delete.
- A decision keeps its source ids and gets `source_state = 'source_deleted'`.
- Inference attestations have no-update and no-delete triggers.

## Objects and derived views

- `meetings`, `segments`, `action_items`, `artifacts`, `decisions`, and `kernel_operations` are durable objects.
- `kernel_journal`, attempt tables, receipts, and checkpoints are durable evidence. Do not rebuild them from a process view.
- `segments_fts` is a search index. Rebuild it from `segments`. Editing it does not change the transcript.
- `kernel_projection_stages` stages a result. It becomes `PUBLISHED` only through its materializer after the terminal receipt.
- A process view shows current state. A stale row does not prove that an effect succeeded.

`kernel_parent_runs.input_json` stores caller input snapshots.
The kernel filter rejects named audio, PCM, and token fields.
It does not reject every prompt or transcript string.

## Startup and recovery

`Database` repairs the shape before it returns access (`holdspeak/db/core.py`).
Then the kernel starts, in this order (`holdspeak/kernel/runtime.py`):

1. Open the journal store.
2. Reconcile abandoned parent runs.
3. Recover inference route executions.
4. Reap expired claims, then recover projection stages.

A restart can turn an unfinished operation into a refusal or `indeterminate`.
It never turns a missing receipt into success.
[KERNEL.md](KERNEL.md) has the state rules.

`holdspeak/runtime_identity.py` records the expected and loaded schema stamps.
It can report a stale bundle, two runtimes, or a schema ahead or behind.
It does not repair the shape and does not refuse a start.

## See also

- [OPERATIONS.md](OPERATIONS.md): doctor, backup, and restart steps.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): symptoms and safe actions.
- [DATA_MODEL.md](DATA_MODEL.md): the tables.
- [SECURITY_MODEL.md](SECURITY_MODEL.md): storage limits.
