# HS-93-06 — A meeting survives real life

- **Project:** holdspeak
- **Phase:** 93
- **Status:** backlog
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

Bundling note: this initial Phase-93 scaffold is intentionally committed with
the HS-93-01 through HS-93-05 in-progress implementation slices because the
owner directed that the complete shared working tree ship together. No story is
marked done; each closure gate remains independent.
