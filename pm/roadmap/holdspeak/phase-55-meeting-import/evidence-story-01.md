# Evidence — HS-55-01: The import engine (file → meeting)

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. What shipped

`holdspeak/meeting_import.py` (~250 lines): `import_meeting(path, *, db,
transcriber, config, title, speaker, tags, started_at, window_seconds,
progress) -> ImportResult`, plus `load_audio` and `MeetingImportError`.

- **Decode:** PCM WAV via the stdlib `wave` module (16/32/8-bit, stereo
  downmixed) — deliberately **not** scipy, which is a dev-only extra; a
  non-PCM WAV falls back to ffmpeg when present. mp3/m4a/aac/ogg/opus/flac/
  webm/mp4 decode by shelling to `ffmpeg -f s16le -ac 1 -ar 16000`
  **iff** ffmpeg is on PATH; otherwise a `MeetingImportError` with the
  install hint. Unsupported suffixes refused with the supported list.
- **Transcriber contract honored:** mono float32 resampled to 16 kHz via the
  existing `_linear_resample_mono` before any `transcribe()` call.
- **Windowed transcription:** ~30 s windows, one `TranscriptSegment` per
  non-empty window stamped with the window's real start/end (last window
  clipped to the true duration); empty windows skipped; an all-empty file is
  refused ("No speech could be transcribed") rather than saving a mystery
  row. Progress callback fires per window.
- **A real meeting:** normal `MeetingState` (`uuid4[:8]`, `started_at` from
  file mtime so old recordings sort where they happened, title from the
  filename, one honest speaker label defaulting to "Recording"), persisted
  by the normal `save_meeting`.
- **Intel mirror:** the exact live conditions (`meeting_session.py` save
  path): intel enabled + deferred → `intel_status="queued"` + enqueue via
  `db.intel.enqueue_intel_job(id, transcript_hash, reason)`; disabled →
  `intel_status="disabled"` with the same detail wording as live.
- The source audio is read and **not retained**.

## 2. Tests (actually run, actually read)

`tests/unit/test_meeting_import.py` — 8 tests: happy path (3 windows,
timestamps `(0,30) (30,60) (60,75)`, title/tags/mtime/duration, persistence +
enqueue), 44.1 kHz stereo downmix/resample asserted on the arrays the fake
transcriber received, empty-window skip + all-empty refusal, the
ffmpeg-absent refusal, the ffmpeg-present decode path, unsupported-format
refusal, intel-disabled (no job, honest status), missing-file + label/title
overrides.

`tests/integration/test_meeting_import_parity.py` — the imported meeting is
indistinguishable downstream: lists via `GET /api/meetings` (title, segment
count, `intel_status="queued"`), full-text search finds its transcript,
detail + markdown export behave like a live meeting.

```
$ uv run pytest -q tests/unit/test_meeting_import.py
8 passed in 0.60s

$ uv run pytest -q tests/integration/test_meeting_import_parity.py
1 passed in 0.59s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2554 passed, 17 skipped in 75.90s (0:01:15)
```

(2545 → 2554: the nine new tests.)

## 3. Notes for HS-55-02

- The engine is FastAPI-free; the route injects `db`, the shared
  `Transcriber`, and the loaded `Config`, and forwards the progress callback
  into whatever status surface the row exposes.
- `ffmpeg_available()` is module-level and monkeypatch-friendly; the API's
  up-front format validation can reuse `load_audio`'s suffix logic (consider
  exporting a `probe_format(path)` if the route wants to refuse before
  reading the body — decide there).
- `python-multipart` is NOT yet a dependency (verified pyproject core deps);
  HS-55-02 must add it for `UploadFile`.
