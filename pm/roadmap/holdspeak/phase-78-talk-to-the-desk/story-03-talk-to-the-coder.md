# HS-78-03 — Talk to the waiting coder

- **Status:** done
- **Severity:** HIGH
- **Depends on:** HS-78-01
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; real audio through the real
  transcriber where the story claims speech works; the demo is the
  closeout's proof; full suite green at ship.

## Done

Shipped. Hold to answer on the coder pull-out (select + remote-inject
through the HSM-13 seam, byte-identical), plus a latent bug fixed: the
desk's coder mapper never read `last_assistant_text`, so a waiting
coder's question never rendered. THE REAL PROOF: a real hook-ingested
waiting Claude (real transcript, real question heuristic), real speech
through real Whisper, the words delivered to the agent seam, `Sent` on
screen. See [evidence-story-03.md](./evidence-story-03.md).
