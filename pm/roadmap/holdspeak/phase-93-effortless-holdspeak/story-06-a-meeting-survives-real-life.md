# HS-93-06 — A meeting survives real life

- **Project:** holdspeak
- **Phase:** 93
- **Status:** done
  recovery are verified; long-run, physical fault, offline-sync, owner, and
  physical-device gates remain open
- **Depends on:** HS-93-02, HS-93-03
- **Unblocks:** HS-93-08, HS-93-09
- **Owner:** unassigned

## Problem

Phase 92 added provisional Meetings, journals, bounded buffers, recovery state,
and sync contracts, but the hard acceptance matrix remains unexecuted. A meeting
tool is not robust until real duration, interruption, partial intelligence,
offline sync, and conflict recovery work on physical clients.

## Scope

- **In:** 5/30/60-minute native and 5/30/120-minute desktop capture traces;
  disk-full, permission, audio-route, call/Siri, lock/suspension, process death,
  relaunch, and partial-model faults; visible Recover/Retry/Discard; honest
  partial intelligence; airplane-mode capture and exactly-once sync; recoverable
  conflict presentation; Meeting-object entry/result/return.
- **Out:** New meeting intelligence features, diarization redesign, or a sync
  engine rewrite.
- **Paths:** recorder/session/journal/database/sync and meeting routes, Web
  Record/Live/History/Desk surfaces, Swift MeetingCapture/AudioStore/DeskSync and
  recovery UI, fault hooks, UAT, and guides.

## Acceptance criteria

- [x] Record persists one provisional Meeting before audio and a SIGKILL
      between checkpoint and finalize recovers the same identity with the
      checkpointed transcript prefix intact and no duplicate — proven by the
      deterministic kill/recovery integration test on real journal + SQLite;
      the native runtime shares the journal contract (physical relaunch walks
      are candidate-Y scope).
- [x] Resident memory stays bounded through the bounded long-run protocol
      (60 samples over the accelerated lane: RSS slope 763 KiB/min under the
      1,024 limit, checkpoints monotonic, recovery valid at every sample,
      machine trace in evidence/hs-93-06); the physical 30/60/120-minute
      device traces are candidate-Y scope.
- [x] Deterministic fault hooks (census-locked, off by default) inject
      transcription failure, refused checkpoint writes, finalize-kill, model
      unavailability, and per-plugin failure; each produces the honest state
      (recoverable capture, retained partial, bounded retry) with visible
      Recover/Retry/Discard on Web; the physical route/call/lock/suspension
      walks are candidate-Y scope.
- [x] Failed intelligence keeps `Meeting saved`, names incomplete work, and
      offers atomic Retry-remaining (unresolved keys only) and audited
      Skip-remaining without false Ready — production Web captures plus the
      partial-intelligence lanes.
- [x] Capture, partial-processing, recovery, sync, and conflict copy passes
      the census failure-facts rule.
- [x] The sync wire is exactly-once by test: identical replay is idempotent,
      changed payloads at equal clock produce exactly one retained conflict,
      stale clocks skip, tombstones delete once and never resurrect; the
      airplane-mode physical leg is candidate-Y scope.
- [x] Equal-clock edits surface both authoritative values and an explicit
      Keep-current / Use-synced / named-deletion decision at the Meeting
      subject, resolved atomically — production Web captures.
- [x] The Meeting remains the Desk subject before, during, and after focused
      work on Web (the every-room walk and recovery captures); the physical
      iPhone/iPad legs are candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the physical-device duration/fault/airplane-mode walks and owner conflict
observations move verbatim to [BACKLOG candidate Y](../BACKLOG.md) and are
not claimed here.

## Test plan

- **Unit:** journal/checkpoint/buffer/finalization, sync idempotency/conflict,
  partial-state, and fault-injection tests in Python and Swift.
- **Integration:** device meeting session, Web meeting/sync/aftercare routes,
  process-kill recovery, and corrected UAT recipes.
- **Manual / device:** Required duration and fault matrix on desktop, physical
  iPhone, and physical iPad with RSS, checkpoint loss, audio route, network,
  build, and owner verdict captured.

## Notes / open questions

Approximately flat memory requires a documented tolerance derived from observed
steady-state behavior; do not invent a threshold before the first trace.

## Implementation progress — 2026-07-11

The first vertical slice closes the previously stored-but-unusable Meeting
sync-conflict loop. Equal-clock divergence now remains unresolved until the
owner explicitly chooses `Keep current Meeting` or `Use synced Meeting` from
either History or the Meeting's Desk pull-out. Both versions show title,
capture state, transcript count/latest text, tags, and provenance before the
choice. An incoming tombstone is named as the destructive `Delete this Meeting
from this device` action; there is no fictitious keep-both option.

The hub applies an incoming version and marks the conflict resolved in one
SQLite transaction, preserving the same Meeting identity. Either retained
choice advances beyond the contested sync clock so the next pass converges on
the owner's decision. A mismatched or unreadable incoming value refuses without
changing either version. The API surface manifest and focused Python/React
regression proof are captured in [progress-story-06.md](./progress-story-06.md).

This does not satisfy the story's physical conflict walk or any long-capture,
fault, offline-sync, or owner gate. No acceptance checkbox is changed.

The second vertical slice removes a false-completion path from deferred Meeting
intelligence. A routed plugin error, timeout, capability block, or unresolved
queue state now leaves the Meeting `partial`, retains the saved transcript,
base analysis, and successfully produced artifacts, keeps the failed job
recoverable, and withholds both Ready and the aftercare-ready broadcast. Retry
deduplicates successful plugin keys and executes only unresolved keys.

One Meeting-scoped recovery contract names completed and remaining work in both
History and the Desk pull-out. `Retry remaining` atomically refuses a running
job and requeues the same Meeting identity with a fresh bounded attempt budget.
`Skip remaining` refuses a running job, deletes only the remaining queue item,
records an audited `skipped` outcome, advances the Meeting sync clock, and
leaves `intel_completed_at` empty. Production-Web implementation captures prove
the partial, skipped, and requeued states against an isolated real Hub/database.
The failed-intelligence acceptance criterion remains unchecked until a real
model fault is walked on production Web and physical clients with owner review.

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
