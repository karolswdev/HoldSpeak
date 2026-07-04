# Phase 23 — Mesh-safe storage (mobile schema safety)

**Status:** in-progress (opened 2026-07-04) — audit theme 6, the safety net for everything
sync touches, opened before the mesh grows more newer-DB peers.

**Last updated:** 2026-07-04 (**OPENED, survey-corrected — half the phase was pre-paid.**
The 2026-06-27 draft predates Wave 4 and Wave 1 of the Equilibrium build waves:
**23-01 and 23-02 shipped in Wave 4** (`SQLiteStorage` reads `user_version` BEFORE
migrate/stamp, refuses a newer-than-build DB with `StorageError.tooNew`, and snapshots a
timestamped backup before the v1→v2 ALTERs — `SQLiteStorageSchemaSafetyTests`, re-run green
on open), and **23-04's live-merge half shipped in Wave 1** (`POST /api/sync/push`
live-merges meetings + artifacts into their real tables; the JSON inbox is an audit trail
now, not the store). The wire pin also largely exists since HS-72-01 (the ChangeSet schema
+ the tri-guard). What actually remains: the readiness/doctor panel (23-03 — the safety
mechanism has ZERO UI surface; `.tooNew` reaches the user as an undifferentiated "Store
unavailable" string), and 23-04's integrity tail — chain/workflow are the two matrix rows
with no push→pull round-trip lock, §11 of the serialization contract still describes a
two-bucket wire, and the §12/agent-schema "manual_context is lossy" finding went stale the
day Phase 77 fixed it. Stories re-grounded below.)

## Why this phase exists

Audit theme 6: *mobile schema safety lags the desktop matrix.* The desktop earned a
safe-by-default schema matrix (refuse-newer / backup-then-apply / no-op / create-fresh) in
Phase 50. When this phase was authored the iPad had none of it; Wave 4 built the mechanism,
and this phase now finishes the job:

- **The mechanism is invisible.** Refuse-newer + backup-then-apply are provider-layer only.
  No view reports store/schema health, `StorageError.tooNew` is not distinguished from any
  other open failure (`MeetingCaptureApp.swift` renders a generic "Store unavailable"), and
  three call sites `try?`-swallow open errors entirely (`DeskHome.swift:239`,
  `ReviewUI.swift:38`, `MeetingCaptureApp.swift:406`). The iPad cannot tell you it is
  healthy — or that it just refused a newer DB to protect it.
- **The sync-integrity matrix has holes.** Chain and workflow ride the generic
  `_MERGEABLE` push path with pull-serialization coverage but no push→pull round-trip /
  LWW / tombstone lock of their own — the audit critic's per-primitive matrix lands here.
- **The pinned contract drifted.** `SERIALIZATION-CONTRACT.md` §11 still describes
  `change_set` as `{meetings, artifacts}` (the live wire carries 10 kinds; §12 knows, §11
  was never back-updated), and §12 + `agent.schema.json` still call
  `Agent.manual_context`/`use_zone_context` "lossy through hub sync" — Phase 77 (db v7)
  fixed that, byte-faithful round-trip test-locked.

## The load-bearing design call

**Mirror the desktop refuse-newer matrix on the iPad, back up before you migrate, and pin
the wire.** The first two clauses are built (Wave 4). The rest: surface the mechanism
honestly (a readiness panel that states store health, schema version, and the refuse-newer
event when it fires — labels, never reassurance prose), close the chain/workflow rows of
the per-primitive round-trip matrix, and make the serialization contract state the wire
that actually ships (§11 current, the stale lossy-finding corrected).

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-23-01 | Refuse-newer on the iPad store — **leads** | done (pre-paid, Wave 4) — [`evidence-story-01.md`](./evidence-story-01.md) |
| HSM-23-02 | Backup-then-apply (timestamped) before migration | done (pre-paid, Wave 4) — [`evidence-story-02.md`](./evidence-story-02.md) |
| HSM-23-03 | The readiness / doctor panel in Settings | todo |
| HSM-23-04 | Sync integrity: the per-primitive round-trip matrix + the serialization-contract pin | in-progress |

## Where we are

Opened 2026-07-04, survey-corrected: **2/4 on open** — 23-01/23-02 shipped in Equilibrium
Wave 4 (evidence recorded from the shipped code + a fresh green run of
`SQLiteStorageSchemaSafetyTests` + `StorageTests`, 8/8). 23-04 is in progress: the
live-merge half shipped in Wave 1 and the HS-72-01 tri-guard pins the envelope; what lands
now is the chain/workflow round-trip rows, the §11 refresh, and the manual_context truth
correction. 23-03 (the doctor panel) follows — it is the phase's only new UI surface.
