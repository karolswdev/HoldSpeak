# Evidence — HS-60-02: Arm, capture, and the pipeline

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

## 1. What shipped

- **`ArmedCapture`** (`wake_word.py`): the post-detection state machine in
  frame-count time — wait for speech onset inside the armed window (RMS
  gate), capture until sustained silence or the utterance cap, yield
  float32 audio or None (the silent disarm). Pure and array-driven in
  tests.
- **The runtime glue** (`web_runtime.py`): `_sync_wake_word()` starts/stops
  the listener to match config — at boot, live on settings-applied, and in
  the shutdown `finally`. `_start_wake_listener()` builds the real engine
  lazily (an honest log + no-op when the extra is missing), opens a
  dedicated 16 kHz int16 InputStream at the 1280-sample hop, and gives the
  listener a **self-healing floor-respecting frame source**: while ANY
  owner holds the audio floor (hotkey, device, meeting, or a wake capture
  itself) the listener pauses (frames drain unscored, the resume re-arms
  the cooldown per HS-60-01); it resumes when the floor frees.
- **`_on_wake_detect`**: acquire the floor as owner `wake` (held floor →
  silent skip, never contend) → the `armed` runtime activity (a NEW
  activity state, added to the registry + the active window policy) + a
  `wake_armed` broadcast → drive `ArmedCapture` from the same frame queue
  under a hard iteration cap (a dead stream can never wedge the floor) →
  release → hand off, or the silent disarm.
- **`_transcribe_wake`**: transcription → the text processor → **the
  normal dictation pipeline** (`run_dictation_pipeline` gained a
  `journal_source` param; wake runs journal as source `wake`). Then the
  fork the phase exists for: `action="preview"` (default) stores a
  one-shot token (`consume_wake_preview` burns it; a new preview
  invalidates the old), broadcasts `wake_preview`, and **never touches
  the typing seam**; `action="type"` (the explicit opt-in) types the
  pipeline result like a hotkey run.

## 2. Tests

`tests/unit/test_wake_runtime.py` — 10 tests: the ArmedCapture matrix
(wait→capture→silence-stop, window expiry, the runaway cap), and the
runtime glue on a bare WebRuntime with a real `VoiceTypingSession`:
detect→arm→capture→hand-off with the floor released; the held-floor
silent skip; the expired-window silent disarm; **preview-never-types**
(typing spy empty; `journal_source="wake"` captured; the broadcast token
consumed once and burned); the type opt-in typing exactly the pipeline
result; new-preview-invalidates-old; disabled-config-constructs-nothing.

One pre-existing test updated: the Phase-52 delegate spy learned the new
`journal_source` kwarg (signature-compatible default; behavior identical).

```
$ uv run pytest -q tests/unit/test_wake_runtime.py
10 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2715 passed, 17 skipped
```

(2705 → 2715.)
