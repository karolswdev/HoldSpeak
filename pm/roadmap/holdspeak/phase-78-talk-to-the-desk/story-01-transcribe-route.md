# HS-78-01 — The transcribe route (local Whisper, no egress)

- **Status:** done
- **Severity:** HIGH
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; real audio through the real
  transcriber where the story claims speech works; the demo is the
  closeout's proof; full suite green at ship.

## Done

Shipped: the runtime verb (one model, one lock, the dictation punctuation
pass; no journaling by design), the on_transcribe seam, and the strict
WAV route (16 kHz mono 16-bit; 16 MB cap; honest 400/413/503; audio never
persisted, nothing egresses). 5/5 with the decoded shape asserted; the
real spoken pass rides the closeout demo. See
[evidence-story-01.md](./evidence-story-01.md).
