# HS-25-05 — Whisper Transcription Timeout

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
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

- [x] Configurable timeout in config with a documented default —
      `ModelConfig.transcribe_timeout_seconds = 120.0` (generous, never clips a
      legitimate long utterance; `<= 0` disables).
- [x] A slow mock transcriber proves the timeout fires
      (`TranscriberTimeoutError`) and the instance is reusable afterwards (the
      controller-level "notify + return to idle" rides the existing
      `except Exception` → `finally: set_state("idle")`; `TranscriberTimeoutError`
      subclasses `TranscriberError` so that handler catches it unchanged) —
      `tests/unit/test_transcribe_timeout.py`.
- [x] No lock held after a timeout: the error raises inside
      `with self._transcription_lock`, which releases on unwind; the HS-25-04
      runtime lock is not held during transcription (it guards the pipeline's
      classify/rewrite, which run *after* transcription).
- [x] Fast/disabled paths unchanged: `<= 0` runs inline; a fast call under the
      timeout returns normally — both covered by tests.

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

## Closeout

Shipped 2026-05-31. See [evidence-story-05.md](./evidence-story-05.md).

Chose the daemon-thread + `join(timeout)` mechanism (over `ThreadPoolExecutor`)
specifically so a timed-out, uninterruptible native call is *abandoned* without
blocking process exit — `ThreadPoolExecutor` would join its worker at
interpreter shutdown and could hang. Hard cancellation of the native backend is
not possible; documented as best-effort (the worker is reclaimed on process exit
/ GC; the next utterance retries on a fresh call).
