# HS-57-03 — API + /history UI

- **Project:** holdspeak
- **Phase:** 57
- **Status:** backlog
- **Depends on:** HS-57-02
- **Unblocks:** HS-57-04
- **Owner:** unassigned

## Problem
The upload affordance says "recording" and the route always builds a Whisper
transcriber. A transcript upload must ride the same lifecycle without the
model load — and the panel must tell the truth about what each kind gives.

## Scope
- **In:**
  - **Route:** `POST /api/meetings/import` branches by suffix — transcript
    uploads run `import_transcript` on the same background thread with the
    same placeholder → `importing` → engine-save / `import_failed`
    lifecycle, and **never construct a transcriber** (asserted by test).
    `started_at_ms` honored. Audio behavior untouched.
  - **UI:** the panel becomes **"Import a recording or transcript"** —
    accept list adds `.vtt,.srt,.txt`, drop copy updated, honest notes per
    kind (recording: ffmpeg/one-label/audio-not-retained, as today;
    transcript: timestamps real only for VTT/SRT, speaker names read from
    the file when labeled, file not retained). Lean, cohesive additions to
    the uncarved history surface; `is:global` rules respected.
- **Out:** docs (HS-57-04); any new status vocabulary or poll mechanism.

## Acceptance criteria
- [ ] A `.vtt` upload 202s, lands `importing`, resolves to a real meeting
      with the file's speakers/timestamps; `_transcriber_factory` is NOT
      called (monkeypatch-asserted); a garbage `.txt` lands
      `import_failed` with the actionable detail and stays removable.
- [ ] An audio upload is byte-identical (existing route tests unmodified).
- [ ] The panel reads "Import a recording or transcript" with the per-kind
      honest notes; accept list extended; page-content locks; screenshots
      reviewed; `npm run build` clean; 0 `_built/` tracked.

## Test plan
- Route integration (transcript happy/failure + no-transcriber assertion +
  audio untouched); page-content locks; a live Playwright upload pass.
  Full suite.

## Notes / open questions
- Transcript imports finish in milliseconds — the importing pill may never
  be observed by a human; that is fine (the lifecycle is for uniformity
  and for failures).
