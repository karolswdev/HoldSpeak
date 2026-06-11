# Evidence — HS-55-02: Import API + background job + CLI

**Date:** 2026-06-11
**Branch:** `phase-55-meeting-import`

## 1. What shipped

**`POST /api/meetings/import`** (`holdspeak/web/routes/meeting_import.py`,
mounted in `web_server._create_app`; `python-multipart>=0.0.9` added to core
deps — it was absent):

- multipart `file` + optional `title` / `speaker` / `tags` (comma-separated)
  / `started_at_ms` (so the browser can pass the file's real last-modified
  time and old recordings sort where they happened);
- **up-front refusal** via the engine's new `validate_format()` (unsupported
  suffix; the honest missing-ffmpeg message) → 400 before any work, no row;
- on accept: the upload spools to a temp file, a **placeholder meeting row
  is saved immediately** with `intel_status="importing"` / "Preparing
  transcription…", and the engine runs on a **daemon thread** — the route
  returns **202** with the meeting id at once;
- the Whisper `Transcriber` is built lazily inside the worker via a
  module-level factory (tests monkeypatch it; no model loads in tests);
- **progress rides the meeting row**: each window updates
  `intel_status_detail` ("Transcribing — window x of y.") using the same
  load → mutate → `save_meeting` pattern the deferred-intel queue uses — so
  `/history` polling needs nothing new (decision recorded per the story
  note: no parallel job API);
- on success the engine's own save resolves the row to the live-mirrored
  `queued`/`disabled` posture; on failure the row is marked
  `intel_status="import_failed"` with the actionable detail; the temp file
  is always deleted.

**`DELETE /api/meetings/{meeting_id}`** (in `routes/meetings.py`): the story
promised failed imports are "deletable via the existing delete path" — it
turned out the repo's `delete_meeting` had **no HTTP route at all**, so the
route was added (the HS-55-03 UI needs it for the remove affordance too).

**Engine additions:** `meeting_id=` parameter (the route pre-allocates the
placeholder's id; `save_meeting` upserts the final state over it) and
`validate_format()`.

**CLI:** `holdspeak import <file> [--title --speaker --tag]`
(`holdspeak/commands/import_recording.py`, wired in `main.py` + the usage
epilog): synchronous, prints per-window progress, reports the intel posture
("queued — process with `holdspeak intel --process`"), exits non-zero on
refusal/failure. Refusal smoke-tested for real:

```
$ holdspeak import /tmp/notaudio.txt
error: Unsupported audio format: .txt. Supported: .wav natively; .aac, .flac,
.m4a, .mp3, .mp4, .oga, .ogg, .opus, .webm with ffmpeg installed.
exit=1
```

## 2. Tests (actually run, actually read)

`tests/integration/test_web_meeting_import_api.py` — 4 tests:

- **Happy path:** 202 → row visible immediately → resolves to
  `queued`/`disabled` with the transcribed segments, title, speaker label.
- **Up-front refusals:** unsupported format and missing-ffmpeg both 400 with
  the actionable error and leave no row behind.
- **Mid-transcription failure:** an exploding transcriber → the row reaches
  `import_failed` with "model fell over" in the detail → `DELETE` removes it.
- **Responsiveness:** a transcriber blocked on an event → the row reports
  `importing` while `GET /api/meetings` keeps answering → release → resolves.

One finding the tests surfaced: the meeting **detail** endpoint serializes
`intel_status` as a nested `{"state", "detail", ...}` object (the list
endpoint uses flat strings) — the tests read the real shape; the HS-55-03 UI
must too.

```
$ uv run pytest -q tests/integration/test_web_meeting_import_api.py \
    tests/integration/test_meeting_import_parity.py tests/unit/test_meeting_import.py
13 passed in 1.54s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2558 passed, 17 skipped in 81.86s (0:01:21)
```

(2554 → 2558: the four route tests.)

## 3. Notes for HS-55-03

- Poll the **detail** endpoint (nested `intel_status.state`/`.detail`) or the
  list payload (flat `intel_status` + `intel_status_detail`) — both carry the
  importing/import_failed states and the window progress text.
- Send `started_at_ms` from `File.lastModified` in the browser.
- The remove affordance for failed imports calls the new
  `DELETE /api/meetings/{id}`.
