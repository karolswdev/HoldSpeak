# HSM-4-02 — Crash recovery (Track E gate closeout)

- **Project:** holdspeak-mobile
- **Phase:** 4
- **Status:** done
- **Depends on:** HSM-4-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

A meeting recording is a long write: segments stream into the store for minutes
or hours. If the app is killed mid-write — OS terminates a backgrounded app, a
crash, a force-quit during recording — the persisted meeting must not be left
partial or corrupt. The charter's Track E gate is exactly this: **full recovery
after crash.** The schema and stores exist after HSM-4-01; this story makes them
durable and proves the gate.

## Scope

- **In:** WAL (write-ahead logging) / journaling configuration on the SQLite
  store so an interrupted write does not corrupt the database; the write/commit
  boundaries during an active recording chosen so a mid-write kill leaves a
  consistent state (no half-written segment, no dangling Meeting); the
  crash-recovery test that kills the process mid-write with segments in flight,
  reopens the store, and asserts the Meeting + its Segments are intact and
  consistent; the Track E gate closeout (mark the gate met with repeatable
  evidence).
- **Out:** the schema/store implementation (HSM-4-01). The version policy
  (HSM-4-03). Encryption-at-rest and the broader hardening scenarios (Phase 11,
  Track L). Sync conflict recovery (Phase 10). Recovery of in-flight *audio*
  buffers that never reached the store — this story covers what the store
  durably commits, not the audio engine's own buffering (Phase 2, Track C).

## Acceptance criteria

Checklist. Merge gate. Each item must be verifiable by reading code or running a
command:

- [ ] The SQLite store is configured with WAL/journaling such that an interrupted
      write cannot leave a corrupt database file (the mode is set in code, not
      assumed default).
- [ ] A repeatable test simulates a real mid-write crash: an active recording is
      streaming Segments, the process is hard-killed (not a graceful close), the
      store is reopened, and the persisted Meeting + already-committed Segments
      are intact and consistent (no partial/corrupt rows, foreign keys hold).
- [ ] The recovery is deterministic about the boundary: it is stated and tested
      which segments are guaranteed durable at kill time (committed) versus which
      may be lost (uncommitted in-flight) — recovery means "no corruption and no
      inconsistency," not "zero data loss of uncommitted writes."
- [ ] The Track E gate ("full recovery after crash") is demonstrated by the test
      and the gate is recorded as met in the phase's exit criteria.
- [ ] The recovery holds on a real iOS target's suspend→terminate path, not only
      the dev host (or, if device proof is deferred, the deferral is recorded with
      a stop signal).

## Test plan

- Unit: WAL/journaling mode is asserted set on a freshly opened store; reopening a
  store after an injected mid-transaction abort yields a valid, consistent DB.
- Integration: drive a recording that writes N Segments, hard-kill the process
  (SIGKILL / app-terminate) between commits, reopen via `IStorage`, assert the
  Meeting and all committed Segments are intact and queryable; repeat across
  several kill points to show it is not flaky.
- Manual / device: on an iPad/iPhone target, start a recording, send the app to
  background and terminate it (or trigger the OS to), relaunch, and confirm the
  meeting is recoverable. Capture the steps and result.

## Notes / open questions

- This is the gate closeout for Phase 4. "Recovery" is proven by a *mid-write
  kill*, not a clean shutdown — a clean-close test does not satisfy Track E (see
  the phase risk table).
- Define "intact" precisely before writing the test: committed rows survive and
  are consistent; uncommitted in-flight writes may be lost; nothing is corrupt.
  Record that definition so the gate is unambiguous.
- WAL leaves `-wal`/`-shm` companion files; confirm they live in the app sandbox
  with the DB and that iOS file-protection/suspension does not strand them.
- If on-device proof can't land in this PR, record it as a deferred item with the
  device stop signal from the phase risk table — do not silently close the gate
  on host-only evidence.
