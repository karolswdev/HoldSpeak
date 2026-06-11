# HS-55-01 — The import engine (file → meeting)

- **Project:** holdspeak
- **Phase:** 55
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-55-02, HS-55-03, HS-55-06
- **Owner:** unassigned

## Problem
The file→transcribe→meeting recipe exists only inside a test harness
(`tests/e2e/test_spoken_meeting_e2e.py:122-223`). There is no production module
that takes an audio file and produces a real, persisted meeting with segments,
timestamps, and the same intel enqueue as a live capture.

## Scope
- **In:**
  - `holdspeak/meeting_import.py`: `import_meeting(path, db, transcriber, *,
    title=None, speaker=None, tags=(), progress=None, ...) -> MeetingState`
    (exact signature implementer's call; transcriber injected for testability).
  - **Decode:** WAV via scipy natively; mp3/m4a/ogg/flac by shelling to
    `ffmpeg` when present on PATH (decode to 16 kHz mono PCM); a clear,
    actionable refusal when the format needs ffmpeg and it's absent. Downmix
    stereo, resample to 16 kHz (`holdspeak/audio.py` has
    `_linear_resample_mono`).
  - **Windowed transcription:** ~30 s windows through
    `Transcriber.transcribe` (timeout applies per window); one
    `TranscriptSegment` per non-empty window with real window start/end
    times; the user's single speaker label (default an honest "Recording").
  - **Persist:** a normal `MeetingState` (id, `started_at` from file mtime,
    ended_at/duration from audio length, title defaulting to the filename)
    via `db.meetings.save_meeting`; enqueue intel under the same conditions
    as `meeting_session.py:1474` (enabled + deferred + non-empty transcript).
  - **Progress callback** (windows done / total) for the CLI and the API job.
- **Out:** the HTTP route + CLI (HS-55-02); UI (HS-55-03); diarization;
  retaining the audio.

## Acceptance criteria
- [x] A generated WAV (tone/silence fixtures) imports end to end with a fake
      transcriber: correct segment count, window timestamps, speaker label,
      title/tags, duration, `started_at` from mtime.
- [x] 44.1 kHz stereo input is downmixed + resampled before transcription
      (asserted via the fake transcriber's received arrays).
- [x] A compressed-format file with ffmpeg absent is refused with an
      actionable error; with ffmpeg present (or faked) it decodes.
      (WAV decodes via the stdlib `wave` module — scipy is dev-only.)
- [x] Intel is enqueued exactly under the live path's conditions; disabled
      intel or an empty transcript enqueues nothing. (All-empty transcripts
      refuse the whole import — no mystery rows.)
- [x] The persisted meeting is indistinguishable downstream: it lists via
      `GET /api/meetings`, exports, and full-text-searches like a live one
      (integration test). (8 unit + 1 parity test; full suite 2554 passed,
      17 skipped — see `evidence-story-01.md`.)

## Test plan
- Unit: `uv run pytest -q tests/unit -k "meeting_import or import_engine"` —
  decode/resample/windowing/refusal/enqueue cases with synthesized WAVs + a
  fake transcriber.
- Integration: import → list/search/export through the web routes.
- Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- Keep the engine free of FastAPI/UI imports — file in, meeting out.
- ffmpeg invocation: decode to a temp WAV (or pipe PCM); clean up the temp
  file; never retain the source audio.
