# Evidence — HS-78-01 — The transcribe route (local Whisper, no egress)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-78-talk-to-the-desk`)

## What changed

- **The runtime verb** (`transcribe_audio`, the dictation-capture mixin):
  the runtime's OWN transcriber (one model, one lock; the MLX pinning
  lives inside `_MlxTranscriber`) + the same punctuation/spoken-symbol
  pass dictation gets. Design call recorded: NO journaling — a
  speak-to-fill is the user typing with their voice, not a dictation run.
- **The seam**: `on_transcribe` through WebRuntimeCallbacks → WebContext
  → the runtime method (the wake/preview callback idiom).
- **The route**: `POST /api/dictation/transcribe` — one WAV body
  (16 kHz mono 16-bit PCM; strict-format 400s name the expectation),
  size-capped at 16 MB (~8 minutes), decoded with the stdlib `wave` into
  the pipeline's float32 shape. Audio is never persisted; nothing
  egresses; the loopback/token posture is the app's own. Headless
  runtimes 503 honestly.

## Verification artifacts

- `tests/unit/test_transcribe_route.py` — **5 passed**: the valid-WAV
  round trip asserting the DECODED SHAPE the runtime receives (float32,
  4000 samples for 0.25 s); the three wrong-format refusals; garbage/
  empty/oversize; the honest 503; and the mixin verb running the real
  pipeline pieces (lock + transcriber + the punctuation pass, proven by
  an upper-casing processor).
- One authoring misstep caught by the run: `Request` was not imported in
  system.py (FastAPI silently degraded it to a required query param —
  422s). The REAL spoken pass rides the HS-78-04 demo by design.
- API manifest regenerated. Full suite: **3100 passed, 37 skipped, 0
  failures** (3095 + the 5 new).

## Acceptance criteria — re-checked

- [x] The route accepts browser-shaped WAV, runs the runtime's own
      transcriber, returns `{text}`; caps + refusals honest; no
      persistence; no egress.
