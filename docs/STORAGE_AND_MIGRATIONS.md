# Storage and migrations

This is a source reconstruction at snapshot
`675401a857b85336d4acaa8c65383dfc9636e4c8` (2026-09-19). The checked-out
source currently has that content; a later branch can drift. The mechanical
table and column inventory is in [schema-inventory.json](generated/schema-inventory.json).
That inventory is generated from the declared `SCHEMA_SQL`. It is a useful
shape index, not proof that every older database has already been reconciled.

## Storage boundaries

The normal runtime uses one SQLite database at
`~/.local/share/holdspeak/holdspeak.db` (`holdspeak/db/core.py:47-49`). The
database is opened with foreign keys enabled, WAL journalling and a five-second
busy timeout (`holdspeak/db/connection.py:7-34`). A connection commits on a
successful context exit and rolls back on an exception
(`holdspeak/db/connection.py:45-64`). The default path is user-local, but the
path can be supplied to `Database`; documentation should not infer a universal
location for alternate deployments.

The database contains several classes of data:

| Class | Examples | Role | Durable source or projection |
| --- | --- | --- | --- |
| Domain objects | `meetings`, `segments`, `action_items`, `projects`, `decisions`, `artifacts` | User records and their provenance | Source of truth for the corresponding domain |
| Runtime queues and ledgers | `intel_jobs`, `intel_job_attempts`, `activity_records`, `kernel_journal` | Work descriptors, attempts and append-only evidence | Durable operational records |
| Kernel authority objects | `kernel_operations`, `kernel_receipts`, `kernel_parent_runs`, `kernel_parent_checkpoints`, grants and schedule delegations | Admission, approval, claim, receipt and restart state | Source of truth for runtime authority |
| Read projections | `segments_fts`, process views, meeting intelligence projections, `kernel_projection_stages` | Search, UI and recovery views derived from canonical records | Rebuildable or receipt-gated according to the owning subsystem |
| Schema machinery | `schema_version`, indexes, triggers, FTS shadow tables | Shape stamp and SQLite maintenance | Metadata; never a migration ledger |

The full application also has separate configuration, secret custody and
browser/native stores. The security boundary and retention claims for those
stores are in [SECURITY.md](SECURITY.md); this document describes the SQLite
runtime only.

## Declared schema and reconciliation

`holdspeak/db/schema.py:1-11` defines `SCHEMA_SQL` and an informational
`SCHEMA_VERSION` (currently 79). The version is not a gate. On open,
`reconcile_schema` compares the live shape with the declared SQL and creates
missing tables, indexes and triggers and adds missing columns. The general
column/table repair preserves unknown tables, but explicit legacy rebuilds
replace intelligence-queue, parent-run, action-item and Thread-part tables;
revised triggers can also be dropped and recreated (`holdspeak/db/reconcile.py:69-606`).
The module docstring’s blanket no-DROP claim does not describe those exceptions.
A newer or older informational
stamp does not by itself prevent opening a database. The reconciliation code
is the authority for current shape repair; the generated inventory is not.

The source order is:

1. Inspect existing tables and run required legacy table rebuilds.
2. Add missing columns before running the declared schema/index script.
3. Refresh revised triggers and run the independent context/watch repair passes.
4. Check the remaining shape and create the acquisition index.
5. On a changed existing file, take an automatic backup, then run the grouped
   data backfills and stamp the informational version.

The automatic backup is **not a guaranteed pre-upgrade snapshot**: schema
changes and independent repair passes already precede that call. For a missing
bookmarks table, the table is recreated before the automatic backup is called.
The [claim registry](../tests/unit/doc_claims/registry.py) binds this example to
an executable probe. Run `holdspeak backup` before upgrading when an original
snapshot is needed. The existing backup-call test proves that backup is called,
not that it contains the original shape.

Some legacy shape changes need an explicit table rebuild or data transformation;
those are code paths in `reconcile.py`, not a promise that arbitrary future
renames are automatic. Existing objects and rows are preserved by the general
policy. Read the concrete reconciliation function before describing a change
as reversible or lossless.

The schema has foreign keys and local triggers. For example, meeting children
normally cascade with a meeting, transcript FTS is maintained by insert,
update and delete triggers, and decisions retain source-deleted provenance
through a trigger (`holdspeak/db/schema.py:24-51,75-85,189-213,381-422`). An
FTS table is a read projection, not a second transcript authority. Kernel
receipts and inference attestations are authoritative evidence; the latter
have database no-update/no-delete triggers (`holdspeak/db/schema.py:2156-2199`).

## What is an object and what is a projection?

The distinction matters during recovery:

- `meetings`, `segments`, `action_items`, `artifacts`, `decisions`, and
  `kernel_operations` are durable objects with identity and lifecycle.
- `kernel_journal`, attempt ledgers, receipts and checkpoints are durable
  evidence. They are not UI caches and must not be regenerated from a current
  process view.
- `segments_fts` is a derived search projection. It can be repaired from
  `segments` by the owning FTS procedure; direct edits do not change transcript
  truth.
- `kernel_projection_stages` is a durable, receipt-gated staging record. It is
  neither an arbitrary cache nor permission to publish: a stage becomes
  `PUBLISHED` only through its registered materializer after the terminal
  receipt.
- Process/read views expose current state from canonical rows and journal
  evidence. A stale process row must not be used to infer a successful effect.
- `schema_version` is an informational observation. It is not evidence that all
  shape work ran on a particular database.

The generic journal records runtime facts, but kernel-owned storage is not
uniformly content-free. `kernel_parent_runs.input_json` stores caller input
snapshots. The recursive key filter rejects named audio/PCM/token fields; it
does not reject every prompt or transcript string (`holdspeak/kernel/model.py:9-13`;
`holdspeak/kernel/parent_run.py:105-106`).

## Backups and restore

`backup_database` uses SQLite's backup API and writes a timestamped sibling
backup (`holdspeak/db/core.py:72-107`). A backup is therefore a snapshot of the
database, including committed WAL state as observed by SQLite. The code does
not claim an application-wide snapshot of audio files, config, browser stores
or People sidecars; those have separate retention and backup boundaries.

Restore validates the candidate, refuses a live owner or an unwritable or
locked target, closes the active connection, creates a safety backup, replaces
the database and removes stale `-wal` and `-shm` sidecars
(`holdspeak/db/core.py:110-202`). Candidate validation precedes replacement. The final copy is not an atomic
rename, so this audit does not claim crash-atomic restore. Restore is a data replacement operation and
must be treated as such by an operator.

The focused backup/restore assertions inspect kept data, a timestamped safety
backup, caller-close-before-restore, and an invalid candidate
(`tests/critical/test_journey_backup_restore.py:28-82`). They were inspected
for this document and were not run in the authoring lane. Despite its name,
`test_an_interrupted_restore_leaves_the_installation_openable` supplies an
invalid candidate; it does not interrupt the final copy. Crash-atomic restore
therefore remains unproved.

## Startup and recovery

`Database` ensures the shape before returning normal access
(`holdspeak/db/core.py:205-269`). The kernel then opens its journal store,
reconciles interrupted parents, recovers inference routes, then recovers
projections (`holdspeak/kernel/runtime.py:173-175`). Projection recovery starts
with liveness reaping (`projection_stager.py:343-346`); do not infer that reaping
precedes inference route recovery. A restart can
therefore change an unfinished operation to a truthful refusal or
`indeterminate`; it must not silently turn an absent receipt into success.
See [KERNEL.md](KERNEL.md) for the state and publication rules.

Runtime identity records the expected and loaded schema observations and can
diagnose a stale bundle, two runtimes, or schema ahead/behind conditions
(`holdspeak/runtime_identity.py:215-354`). This diagnostic does not replace
shape reconciliation and does not, by itself, refuse startup.

## Tests and evidence boundary

The schema-policy assertions establish fresh current stamping, no-op opens,
opening a newer informational stamp without data loss, missing table/column
self-healing, preservation of orphan objects/rows and timestamped backup
siblings (`tests/unit/test_db_schema_policy.py:53-220`). Those are inspected
assertions, not a run result. No tests were run for this documentation lane.

The current source does not provide a general rollback migration chain. It
provides additive reconciliation plus selected shape/data repairs. Unknowns
that require a production database inspection include the exact pre-reconcile
shape, whether all historical backfills have run, and whether external files
were backed up with a database snapshot. Do not report those as known from
`SCHEMA_VERSION` alone.

## Operator links

- [OPERATIONS.md](OPERATIONS.md) gives the bounded doctor, backup and restart
  procedures.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) maps symptoms to evidence and
  safe next actions.
- [DATA_MODEL.md](DATA_MODEL.md) describes the data rows represented by this
  store.
- [SECURITY_MODEL.md](SECURITY_MODEL.md) links the existing security contract
  and records storage limits.
