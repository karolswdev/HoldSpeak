# HS-93-06 — A meeting survives real life

- **Project:** holdspeak
- **Phase:** 93
- **Status:** in progress — explicit Web/Hub conflict and partial-intelligence
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

- [ ] Record persists one provisional Meeting before audio on both runtimes;
      Stop, kill, and recovery finalize or discard that same identity without
      duplicate objects.
- [ ] Resident memory remains approximately flat in the required duration matrix
      and loss is bounded to the documented checkpoint interval with raw traces.
- [ ] Disk, permission, route, interruption, lock, suspension, kill, and relaunch
      faults produce visible Recover/Retry/Discard state and never silent loss or
      false completion.
- [ ] Failed intelligence keeps `Meeting saved`, names incomplete work, and
      supports Retry remaining/Skip without claiming Ready or 100 percent.
- [ ] Capture, partial-processing, recovery, sync, and conflict copy follows
      `copy-contract.md`: concise state, retained material, exact missing work,
      and next action without storytelling or false celebration.
- [ ] An offline native Meeting syncs exactly once to Web with transcript timing,
      provenance, partial state, artifacts, and aftercare intact.
- [ ] Equal-clock or concurrent edits surface both authoritative values and an
      owner-visible recovery decision; no scenario claims keep-both unless a real
      additional object is created.
- [ ] The Meeting remains the Desk subject before, during, and after focused
      capture/archive work on Web and physical iPhone/iPad.

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
