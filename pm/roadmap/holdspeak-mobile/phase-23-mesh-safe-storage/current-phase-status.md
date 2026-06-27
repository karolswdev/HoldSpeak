# Phase 23 — Mesh-safe storage (mobile schema safety)

**Status:** planned — independent safety net; schedule before the mesh grows more
newer-DB peers. Stories detailed on open.

**Last updated:** 2026-06-27 (**authored** from the parity audit, theme 6 + the sync-integrity
footnotes.)

## Why this phase exists

Audit theme 6: *mobile schema safety lags the desktop matrix.* The desktop earned a
safe-by-default schema matrix (refuse-newer / backup-then-apply / no-op / create-fresh) in
Phase 50. The iPad has none of it:

- **The iPad store silently downgrade-stamps a newer DB.** `SQLiteStorage.swift:51-61`
  migrates only `userVersion < 2`, then **unconditionally stamps `user_version = 2`** — the
  exact data-loss case desktop refuses. As sync brings a newer-build peer's DB into reach,
  this is a live data-loss risk.
- **No backup-then-apply.** The v1→v2 ALTERs run in place with no timestamped backup.
- **No doctor / readiness panel.** No view reports mic permission, model presence, store/schema
  health, or app version — the iPad cannot tell you it is healthy.

This phase also absorbs the audit's two **sync-integrity** footnotes (filed low-severity but
real): `/api/sync/push` inboxes meetings/artifacts to a JSON inbox rather than merging them
live; and the serialization contract (ID/timestamp/egress-field/`intel_status` nesting,
`source_type` "card" vs "input") is unpinned. Per the EQUILIBRIUM rule, the desktop is audited
here, not assumed.

## The load-bearing design call

**Mirror the desktop refuse-newer matrix on the iPad, back up before you migrate, and pin the
wire.** Read `user_version` *before* migrate/stamp; throw `StorageError.tooNew` and refuse to
open for writes when it exceeds `schemaVersion`. Copy the store to a timestamped backup before
`migrateIfNeeded`. Add an honest readiness card. Then close the sync-integrity holes so content
primitives round-trip on push and the wire shape is pinned across all four surfaces (the
per-primitive matrix explosion the audit critic recommended lives here as the integrity check).

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-23-01 | Refuse-newer on the iPad store — **leads** | todo |
| HSM-23-02 | Backup-then-apply (timestamped) + minimal backup/restore | todo |
| HSM-23-03 | The readiness / doctor panel in Settings | todo |
| HSM-23-04 | Sync integrity (push live-merge) + the serialization-contract pin | todo |

## Where we are

Not started. **23-01 leads** (it is the data-loss stopper). 23-04 is where the audit critic's
"explode the Primitive Framework into per-primitive CRUD/run/sync/egress rows" lands — as a
sync-integrity conformance pass (Note / KB / Directory / Agent / Chain / Workflow each
round-trip cleanly), not a new phase.
