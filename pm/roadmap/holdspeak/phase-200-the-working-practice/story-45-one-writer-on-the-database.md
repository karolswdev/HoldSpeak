# HS-200-45: One writer on the database, or a safe second one

- **Project:** holdspeak
- **Phase:** 200
- **Status:** ready
- **Depends on:** HS-200-02
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** the 2026-09-13 operational-surface audit §10.1 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`)

## Problem

**The MCP sidecar is a second, unsynchronized writer on the same SQLite file the
hub owns**, and nothing in the product prevents it.

- `holdspeak/mcp/tools.py:12` imports `get_database` and composes services
  directly; `db/core.py:46` resolves `~/.local/share/holdspeak/holdspeak.db` with
  **no env override**. Every sidecar start runs `_ensure_schema` →
  `reconcile_schema`, a write transaction.
- **`PRAGMA journal_mode` on the owner's real database is `delete`, not WAL.**
  `holdspeak/db/connection.py:3` claims "WAL pragmas"; `:25-27,41-43` set only
  `foreign_keys=ON`. There is no `busy_timeout` and no `isolation_level` anywhere
  in the package. (The only `journal_mode=WAL` is `holdspeak/people/store.py:407`,
  the separate encrypted People store.)
- **An owner lock exists and the sidecar never takes it.**
  `holdspeak/runtime_lock.py:1-27` is an exclusive `flock` whose docstring says
  *"C10 forbids introducing a multi-writer SQLite arrangement at all."*
  `grep -rn "runtime_lock\|claim_runtime\|flock" holdspeak/mcp/` → **0 hits**.
  Only the hub claims it (`runtime/ownership.py:36,47-51`).

`sqlite3.OperationalError: database is locked` already appears in E2E runs. HS-200-02
built runtime identity and a lock precisely so a second hub refuses to start; the
sidecar walks around it.

Related, and the reason this is not merely theoretical: this repo's `.mcp.json`
carries **no `env` block**, so any agent session with that server enabled opens
the owner's live database. That file is the owner's configuration and this story
does not change it; the product-side defect is that nothing stops it.

## Scope

Decide and implement the writer discipline: either the sidecar becomes a client
of the running hub, or concurrent access is made actually safe (WAL, busy
timeout, and the lock honoured), and a sidecar that cannot be safe refuses with a
sentence naming why.

Implementation seams: `holdspeak/db/connection.py` (pragmas);
`holdspeak/db/core.py`; `holdspeak/mcp/server.py` and `tools.py` (startup);
`holdspeak/runtime_lock.py`; `docs/MCP_SIDECAR.md`.

Out: changing what the MCP tools do. Out: editing the owner's `.mcp.json`.

## Acceptance criteria

- [ ] The chosen discipline is named and argued in the evidence, with the
      rejected option and why — hub-client versus safe-concurrent is a real
      architectural fork, not a detail.
- [ ] `journal_mode` and `busy_timeout` match what `db/connection.py`'s own
      docstring claims, or the docstring is corrected. Code and comment agree.
- [ ] A sidecar started against a database a hub already owns either participates
      safely or refuses with a sentence naming the owner and the remedy — never a
      silent second writer.
- [ ] An existing database is migrated to the chosen journal mode without data
      loss, proven on a COPY of a real database, never on the owner's.
- [ ] A fence test reproduces the contended-write failure against the pre-fix
      tree and passes after.
- [ ] `docs/MCP_SIDECAR.md` states the actual arrangement, including what the
      sidecar assumes about being in-process.

## Test plan

Planned suite: `phase200_one_writer`. Drive a real hub and a real sidecar against
one temporary database; assert the outcome the ruling promises. Never touch
`~/.local/share/holdspeak/holdspeak.db`.

## Notes / open questions

The audit also found that several MCP tools silently mean something different
without a hub: `meeting.start_capture` returns an error, and
`project.steward.trigger` returns `{"success": false, "code":
"scheduler_not_wired"}` with `isError: false` — a soft refusal a caller reads as
success. Fold the honest-refusal half in here if it is cheap; otherwise ledger it.
