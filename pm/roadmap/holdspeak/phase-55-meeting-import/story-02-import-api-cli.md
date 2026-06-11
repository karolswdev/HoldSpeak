# HS-55-02 — Import API + background job + CLI

- **Project:** holdspeak
- **Phase:** 55
- **Status:** done
- **Depends on:** HS-55-01
- **Unblocks:** HS-55-03, HS-55-06
- **Owner:** unassigned

## Problem
The engine needs callers. The web server has no upload route anywhere
(greenfield multipart), and an hour-long file takes minutes of Whisper — a
synchronous route would block or time out. The CLI is the right tool for huge
files and headless machines.

## Scope
- **In:**
  - `POST /api/meetings/import` (multipart: `file`, optional `title`,
    `speaker`, `tags`): validates the format up front (including the honest
    ffmpeg refusal), creates the meeting row **immediately** in a visible
    importing state, runs the engine on a **background thread** (the event
    loop stays responsive; per-window timeouts already guard hangs), updates
    progress as windows land, finishes by enqueueing intel; on failure the
    meeting is marked honestly (clear detail, deletable via the existing
    delete path).
  - **Status surface:** the importing/failed/complete state + progress
    readable through the existing meeting list/detail payloads (so `/history`
    polling stays trivial) — document the exact shape in evidence.
  - Verify/add the `python-multipart` dependency in `pyproject.toml`.
  - **CLI:** `holdspeak import <file> [--title --speaker --tag ...]` —
    synchronous, prints window progress, exits non-zero on refusal/failure;
    same engine, `holdspeak/commands/` pattern.
  - Doctor stays honest: if doctor reports optional capabilities, ffmpeg
    presence is worth a line (cheap; skip if it doesn't fit doctor's shape).
- **Out:** the UI (HS-55-03); concurrent-import queueing beyond "one thread
  per request" (a simple in-flight guard is fine); auth changes (loopback
  posture unchanged).

## Acceptance criteria
- [x] Uploading a small WAV returns fast with a meeting id; the row is
      visible in importing state; polling shows progress; the final state has
      segments + intel queued (integration test with a fake/quick
      transcriber). (202 + immediate row + progress in
      `intel_status_detail`.)
- [x] A bad/unsupported file fails the request (or the job) with an
      actionable message; a mid-transcription failure marks the meeting
      failed-honestly and leaves no half-meeting mystery row.
      (`import_failed` + detail; removable via the **new**
      `DELETE /api/meetings/{id}` — the repo's `delete_meeting` had no HTTP
      route at all, so it was added.)
- [x] The web server answers other routes while an import is running
      (test: poll during a slow fake transcription).
- [x] `holdspeak import` round-trips a WAV from the shell with progress
      output and correct exit codes. (Engine path covered by tests; the
      refusal path smoke-tested for real — exit 1 with the actionable
      message. The full real-Whisper round-trip is the closeout dogfood.)
- [x] `python-multipart` declared; `uv pip install -e .` resolves
      (python-multipart==0.0.32 installed). (13 import tests green; full
      suite 2558 passed, 17 skipped — see `evidence-story-02.md`.)

## Test plan
- Integration: route happy path / refusal / failure / status progression /
  responsiveness-under-import; CLI via the engine with a fake transcriber.
- Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- Prefer riding the meeting row for status over a parallel job API; if a tiny
  `GET /api/meetings/{id}/import-status` proves cleaner, justify in evidence.
