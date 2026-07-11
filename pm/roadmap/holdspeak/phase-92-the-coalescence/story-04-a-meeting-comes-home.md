# HS-92-04 — A meeting survives and comes home

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress (pre-close implementation; long-run/fault/physical sync walk pending)
- **Depends on:** HS-92-01, HS-92-02
- **Unblocks:** HS-92-05, HS-92-09, HS-92-10
- **Owner:** unassigned

## Problem

Both primary clients hold capture hostage to a clean Stop. Native capture grows
roughly 115 MB/hour in raw PCM before overhead, desktop dual-stream float capture
roughly 461 MB/hour, and the durable meeting is created at Stop. Native Desk
sync emits no meetings, and partial native intelligence can fail then display
`Ready`. A meeting journey cannot drive adoption if interruption can erase it
or its result cannot return across devices.

## Scope

- **In:** Shared append-only capture-journal/provisional-meeting contract;
  incremental native and desktop persistence; bounded live windows and memory;
  recover/discard; honest audio retention; partial post-processing state;
  capture-store participation in native sync; Meeting/Transcript/Artifact
  identity and aftercare return to both Desks; conflict and deletion-boundary
  behavior; real-device/fault UAT.
- **Out:** Identical desktop/native audio sources; indefinite background capture
  without OS proof; guaranteed deletion from external services/backups; a new
  meeting home above the Desk.
- **Paths:** `holdspeak/meeting_recorder.py`, `holdspeak/meeting_session/`,
  `holdspeak/db/core.py`, `holdspeak/web/routes/meetings/`,
  `holdspeak/web/routes/sync.py`, `web/src/desk/components/RecordOrb.tsx`,
  `web/src/desk/components/Pullout.tsx`, `web/src/pages/LivePage.tsx`,
  `web/src/pages/HistoryPage.tsx`,
  `apple/Sources/RuntimeCore/Capture/MeetingCapture.swift`,
  `apple/Sources/RuntimeCore/Capture/MeetingAudioStore.swift`,
  `apple/Sources/RuntimeCore/Sync/`, `apple/App/MeetingCapture/DeskSync.swift`,
  and meeting/sync/fault tests and UAT scenarios.

## Acceptance criteria

- [x] Record creates one provisional durable Meeting before accepting audio on
      both runtimes; periodic audio/transcript checkpoints are atomically
      recoverable and Stop finalizes the same ID.
- [ ] 60-minute native and 120-minute desktop dual-stream captures keep resident
      memory approximately flat and preserve all content up to a documented
      bounded checkpoint after forced termination.
- [ ] Disk-full, permission revocation, audio-route change, lock/suspension,
      process death, and relaunch produce a visible Recover/Retry/Discard state;
      the meeting never silently disappears or duplicates.
- [ ] Failed intelligence keeps `Meeting saved`, names completed/failed steps,
      offers Retry remaining/Skip, and never backfills progress to `Ready` or
      100 percent.
- [ ] A Meeting captured offline in the canonical Swift app syncs exactly once
      after reconnect and appears on Web Desk with title, transcript timing,
      speakers, provenance, artifacts/partial state, and aftercare intact.
- [ ] Concurrent title/content changes follow a documented conflict rule with a
      recoverable losing version; UAT no longer claims keep-both unless the
      product actually creates it.
- [ ] The Meeting object is the Desk entry and return point; Transcript and
      aftercare remain owned projections, focused Live/Archive rooms preserve
      context, and retained artifacts materialize with lineage.

## Test plan

- **Unit:** New shared journal/recovery tests plus `uv run pytest -q tests/unit/test_meeting_state.py tests/unit/test_meeting_chunks.py tests/unit/test_audio_source_contract.py tests/unit/test_db_schema_policy.py tests/unit/test_web_routes_sync.py`; focused Swift `MeetingCapture`, `MeetingAudioStore`, sync, interruption, and schema tests.
- **Integration:** `uv run pytest -q tests/integration/test_meeting_session_intent_config.py tests/integration/test_web_meeting_aftercare_api.py tests/integration/test_primitive_framework_sync.py tests/integration/test_device_meeting_session.py tests/e2e/test_spoken_meeting_e2e.py`; corrected UAT meeting/sync/fault recipes.
- **Manual / device:** Physical iPhone/iPad and desktop long-run matrix at 5, 30,
  60, and desktop 120 minutes; force kill, disk full, call/Siri/route change,
  lock, offline/reconnect, partial model failure, and Web return screenshots.

## Notes / open questions

This is one vertical user outcome across two runtimes. If implementation cannot
ship atomically, use additive feature flags behind the same story/PR and do not
expose provisional capture as complete until both recovery and migration paths
are proven.

## Implementation evidence — 2026-07-10

- Desktop and native now persist the provisional Meeting before opening capture,
  append audio to fsynced bounded-loss journals, checkpoint transcript state,
  finalize the same ID, and retain explicit recovery state on failure.
- Both recorders release committed PCM: desktop retains only the transcription
  interval plus overlap, while Swift retains only its active tail; native WAV
  finalization/recovery streams from disk rather than rebuilding the take in RAM.
- Native Meetings now enter `DeskSyncStore`, preserve provenance/capture state,
  persist pulled Meetings into the capture-owned SQLite store, propagate
  tombstones, and use a real modification clock; equal-clock divergent desktop
  merges keep the losing value in `meeting_sync_conflicts`.
- Web History/Desk and the native recent-Meeting list expose incomplete state;
  Web recovers the last atomic checkpoint, and native offers accessible
  Recover/Discard actions after relaunch. Long-take intelligence is marked
  partial/queued instead of false Ready when full-take diarization is deferred.
- Automated proof green: focused Python persistence/schema/session and
  sync/Web integration suites; the 525-test Swift package suite (9 documented
  skips); React typecheck/focused tests/production build; and the production iOS
  host build (with the repository's documented LLM macro workaround).
- Still required before completion: physical 60-minute native / 120-minute
  desktop RSS traces; disk-full, permission, route, lock/suspension and kill
  matrix; airplane-mode capture then exactly-once Web return; partial-model
  Retry/Skip walk; concurrent edit/conflict recovery walk; screenshots and owner
  verdict. None is inferred from automated checks.
