# HS-25-05 — Whisper Transcription Timeout

- **Project:** holdspeak
- **Phase:** 25
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-25-07
- **Owner:** unassigned

## Problem

`Transcriber.transcribe` (`transcribe.py:329`, backend impls at `:195` and
`:272`) has no timeout. If a model hangs — bad weights, a stuck MLX/llama call,
a wedged backend — the transcription thread blocks indefinitely and the user
gets no text and no error. The hot path should fail safe and tell the user, not
hang.

## Scope

### In

- Add a configurable transcription timeout (sensible default; `0`/unset =
  disabled to preserve current behavior where desired).
- On timeout: abandon the call without wedging the controller, notify the user
  (same notification surface used for transcription failures), and return the
  pipeline to idle so the next utterance works.
- Make sure a timed-out call cannot leave the LLM/transcription locks held
  (coordinate with HS-25-04).

### Out

- Cancelling the underlying native inference mid-flight if the backend can't be
  interrupted — document the best-effort behavior instead (thread abandoned,
  resources reclaimed on process exit / next call) rather than promising hard
  cancellation.
- Streaming/partial transcription.

## Acceptance criteria

- [ ] A configurable timeout exists in config with a documented default.
- [ ] A test with a slow/hung mock transcriber proves the timeout fires, the
      user is notified, and the controller returns to idle (a subsequent
      utterance transcribes normally).
- [ ] No lock (`_transcription_lock` or any HS-25-04 runtime lock) remains held
      after a timeout.
- [ ] Default behavior with a fast transcriber is unchanged (no added latency).

## Test plan

- Unit: `uv run pytest -q tests/ -k "transcribe and timeout"` — inject a mock
  transcriber that sleeps past the timeout; assert notify + idle recovery + next
  call succeeds.
- Integration: `uv run pytest -q tests/ -k controller` stays green.
- Manual: n/a (covered by tests + HS-25-07 dogfood).

## Notes / open questions

- Decide the timeout mechanism (watchdog thread + abandon vs. executor with
  `future.result(timeout=...)`); the executor approach composes more cleanly
  with the existing daemon-thread model in `controller.py`.
- Default value: long enough not to clip legitimate long utterances on slower
  backends (faster-whisper medium), short enough to catch a true hang.
