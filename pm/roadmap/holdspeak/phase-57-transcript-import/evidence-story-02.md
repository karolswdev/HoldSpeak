# Evidence — HS-57-02: The engine path + CLI

**Date:** 2026-06-11
**Branch:** `phase-57-transcript-import`

## 1. What shipped

**One persistence tail, two callers** (`holdspeak/meeting_import.py`):
- The tail of `import_meeting` (state → live-mirrored intel posture →
  `save_meeting` → `enqueue_intel_job` → `ImportResult`) factored verbatim
  into `_persist_import(...)`. The audio path now calls it with its window
  counts — **byte-identical behavior, its tests pass unmodified** (the
  whole `tests/unit/test_meeting_import.py` file is untouched by this
  story and green).
- **`import_transcript(path, *, db, config, title, speaker, tags,
  started_at, meeting_id)`**: read (UTF-8, errors replaced) → parse
  (HS-57-01; `TranscriptParseError` re-raised as the engine's
  `MeetingImportError`, so callers have one error type) → honest segments
  (the file's real cue timestamps for VTT/SRT, the parser's synthetic
  ordering for TXT; the file's speaker labels with the user/`Transcript`
  fallback) → the shared tail. `started_at` defaults to file mtime;
  `ended_at`/duration from the last cue. The file is not retained.
- `ImportResult` stays truthful for transcripts: `windows_total` /
  `windows_empty` are 0 (no transcription happened) and a new additive
  `speakers_found` carries the file's labels (empty for audio).
- `validate_format` learns `.vtt/.srt/.txt` (no decoder dependency); the
  audio messages and `load_audio`'s own audio-only refusal are untouched.
  `is_transcript_filename()` is the branching helper route + CLI share.

**CLI** (`holdspeak/commands/import_recording.py`): `holdspeak import
notes.vtt` branches before any model load — no `Transcriber` is constructed
(monkeypatch-asserted: the transcript path works even when the transcription
stack is broken), prints segment count, duration, the file-carried speakers,
and the intel posture.

## 2. Tests

`tests/unit/test_transcript_import_engine.py` — 12 tests: VTT import with
real timestamps + file speakers + voice continuity on the saved segments,
TXT synthetic ordering + fallback speaker, FTS reachability of the imported
text, intel-disabled → no job, zero-cue refusal **with nothing persisted**,
missing-file refusal, mtime default + explicit `started_at`, the
no-transcriber guarantee, `validate_format` trio + audio-untouched, the
suffix helper.

One deliberate test edit outside the new file: the Phase-55 route test
`test_unsupported_format_and_missing_ffmpeg_refuse_up_front` used `.txt` as
its "unsupported format" fixture — `.txt` deliberately stopped being
unsupported in this story, so the fixture became `.pdf` (the test's intent,
"unsupported formats refuse up front", is preserved; the audio engine test
file itself is untouched).

```
$ uv run pytest -q tests/unit/test_transcript_import_engine.py tests/unit/test_meeting_import.py
20 passed in 0.89s        # 12 new + the audio engine file, unmodified
$ uv run pytest -q tests/integration/test_web_meeting_import_api.py
4 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2636 passed, 17 skipped
```

(2624 → 2636.)
