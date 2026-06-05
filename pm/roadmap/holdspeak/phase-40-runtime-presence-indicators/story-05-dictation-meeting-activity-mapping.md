# HS-40-05 — Dictation + Meeting Activity Mapping

- **Project:** holdspeak
- **Phase:** 40
- **Status:** implemented in `/tmp`
- **Depends on:** HS-40-01, HS-40-03, HS-40-04
- **Unblocks:** HS-40-06
- **Owner:** unassigned

## Problem

The indicator is only useful if the state changes line up with real HoldSpeak
work. Voice typing has a fast press/release/transcribe/type lifecycle, while
meeting mode has longer live/saving/intel/plugin/proposal phases. Those events
need to map into the shared activity model with clear labels and error
attribution.

## Scope

- **In:**
  - Map hotkey/device dictation: press accepted, recording, release, short
    recording ignored, transcription, pipeline processing, typing/tmux
    delivery, idle, and errors.
  - Map meeting lifecycle: start accepted/rejected, live recording, waiting
    for first segment, segment arrival, intel live/queued/running/error,
    plugin jobs, actuator proposal arrival, stopping/saving, saved, and errors.
  - Reuse existing `runtime_status["last_transcription"]`, transcription
    status, `last_error`, meeting broadcasts, plugin job summaries, and Phase
    39 metadata where available.
  - Keep snippets privacy-safe: truncate text and avoid displaying rejected
    secrets.
- **Out:**
  - Changing dictation routing/rewriting behavior.
  - Changing meeting intel/plugin/artifact data shapes.
  - Persistent dictation history.

## Acceptance Criteria

- [ ] A normal hotkey dictation cycle visibly advances and returns to idle
      after typing or an empty/no-op transcription.
- [ ] Errors are attributed to recorder, transcriber, pipeline/runtime, text
      injection/tmux delivery, meeting start/stop/save, or intel/plugin work
      when possible.
- [ ] Pipeline-disabled users still get basic capture/transcribe/type status.
- [ ] Meeting status appears immediately on start, before the first transcript
      segment arrives.
- [ ] Proposal/intel/plugin/saving states update without a page reload and
      without changing plugin contracts.

## Test Plan

- Unit: fake event sequences for dictation and meeting mapping.
- Backend: focused `WebRuntime` tests with fake recorder/transcriber/typer or
  injected callbacks where seams exist.
- Frontend/native: event playback fixture consumed by HS-40-06.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / Open Questions

- Phase 39 telemetry is optional input. If it is present, expose better
  pipeline detail; if not, show coarser `processing`.
- 2026-06-05 — Implemented in `/tmp`: activity mapping now covers
  transcription model warming/loading/error, hotkey unavailable/busy, device
  busy/no-reply-target/start failures, meeting segment capture, intel streaming,
  intel complete, action proposals, meeting saving, and meeting saved. Desktop
  policy was corrected so `meeting_live` is a transient linger notification,
  not a persistent meeting-long overlay. Remaining verification: real flow
  smoke under HS-40-06, plus any Phase-39 telemetry enrichment after that phase
  settles.
