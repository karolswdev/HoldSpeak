# Evidence — HS-25-05 — Whisper Transcription Timeout

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

`Transcriber.transcribe` is now bounded by a configurable timeout. A hung model
no longer freezes the pipeline: the call is abandoned, a `TranscriberTimeoutError`
is raised (caught by the controller's existing handler → notify + return to
idle), and the next utterance retries.

## Files touched

- `holdspeak/transcribe.py` — `TranscriberTimeoutError(TranscriberError)`;
  `Transcriber(timeout_seconds=…)`; `transcribe()` runs the backend on a daemon
  worker and `join(timeout)`s it; on timeout raises (worker abandoned, never
  blocks process exit). `import threading`.
- `holdspeak/config.py` — `ModelConfig.transcribe_timeout_seconds = 120.0`
  (generous default; `<= 0` disables).
- `holdspeak/controller.py` — `_ensure_transcriber` passes the configured timeout.
- `tests/unit/test_transcribe_timeout.py` — **new**, 4 cases.

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_transcribe_timeout.py tests/unit/test_config.py
65 passed
  - slow impl (5s) + 0.1s timeout → TranscriberTimeoutError ("abandoned"),
    instance reusable afterwards (fast call returns "done")
  - fast impl under timeout → returns normally
  - timeout <= 0 → runs inline (no worker)
  - backend error propagates through the timeout path

$ uv run ruff check holdspeak/transcribe.py holdspeak/config.py \
    holdspeak/controller.py tests/unit/test_transcribe_timeout.py
All checks passed!

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
9 failed, 1860 passed, 13 skipped
  (+4 vs HS-25-04 baseline; the 9 are the same documented pre-existing failures.)
```

## Lock-safety argument (criterion 3)

A timeout raises inside the controller's `with self._transcription_lock:` block,
so the lock releases as the exception unwinds (then `finally: set_state("idle")`).
The HS-25-04 runtime lock is **not** held during transcription — it guards the
dictation pipeline's `classify`/`rewrite`, which run *after* `transcribe()`
returns. So neither lock can be stranded by a transcription timeout.

## Acceptance criteria — re-checked

- [x] Configurable timeout + documented default (120s; `<= 0` disables).
- [x] Timeout fires on a slow mock; instance reusable; controller notify+idle via
      the existing handler (TranscriberTimeoutError ⊂ TranscriberError).
- [x] No lock stranded after a timeout (argument above).
- [x] Fast/disabled paths unchanged.

## Deviations from plan

Mechanism is a daemon thread + `join(timeout)` rather than `ThreadPoolExecutor`
(which would join workers at interpreter exit and could hang on an abandoned
native call). Hard cancellation isn't possible; documented as best-effort.

## Follow-ups

None.
