# Evidence — HS-63-06: Closeout: the live boot proof

**Date:** 2026-06-12
**Verdict:** done — and the story earned its existence twice over: the live
boot proof caught **two pre-existing production bugs** that three phases of
green suites had masked, both in the live meeting path that no dogfood had
exercised since Phase 60.

## The two bugs (both pre-existing, both verified against the originals)

1. **Live meeting start has been broken since Phase 60.** Commit `db8ef3b`
   (HS-60-03) added `on_wake_type=self._type_wake_preview` to TWO call
   sites: correctly to `WebRuntimeCallbacks`, and wrongly to the
   `MeetingSession(...)` constructor — which never accepted that kwarg.
   Every real meeting start through the web runtime raised a TypeError
   ("on_start failed"), invisible to the suite because the
   FakeMeetingSession stub accepts `**kwargs`, and invisible to dogfoods
   because none since Phase 60 started a meeting via `run_web_runtime`.
   Fixed (the stray kwarg removed) and locked by
   `tests/unit/test_meeting_glue_session_kwargs.py`, which binds the real
   call site's kwargs to the real constructor's signature via AST +
   inspect — a permissive fake can never hide a stray kwarg again.
2. **Transcriber construction was racy — with a process-fatal blast
   radius.** With the start bug fixed, meeting STOP killed the runtime:
   `libc++abi: terminating … There is no Stream(gpu, 3) in current
   thread` (the Phase-60 MLX crash class, one level up). Root cause,
   proven by probe runs (the crashing run loaded the model TWICE, the
   passing run ONCE): the boot-time warmup thread and the meeting-start
   route thread race the unlocked check-then-construct in
   `_ensure_transcriber_loaded`; two `_MlxTranscriber` instances exist;
   mlx_whisper's process-level model cache binds the model to the first
   instance's pinned thread; the second instance's transcribe is
   cross-thread and fatal. Fixed with a dedicated leaf lock
   (`_transcriber_init_lock` — NOT `transcription_lock`, which the warmup
   already holds and would deadlock) and locked by
   `tests/unit/test_transcriber_init_race.py` (8 threads, one
   construction).

## The live trace (`dogfood_story06.py` — 8/8 PASS)

The REAL entry path (`run_web_runtime` in a subprocess, the same call the
CLI makes), driven over HTTP + Chromium: `/api/state` answers; a meeting
starts, runs on the real recorder + the real MLX Whisper, stops, and
persists through the carved save path (1 in the archive); a dictation
dry-run flows the pipeline route; the cockpit loads with zero page
errors; SIGTERM exits 0 (the signal path stayed in the core).

## Phase exit

- Full suite: **2775 passed, 17 skipped** (+2: the two new regression
  locks; +7 total this phase with the guard).
- `final-summary.md`; BACKLOG **E flipped to shipped**; README cadence;
  PR merged on green; memory updated.
