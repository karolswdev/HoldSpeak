# HS-78-02 — Speak-to-fill on every desk input

- **Status:** done
- **Severity:** HIGH
- **Depends on:** HS-78-01
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## What

(The contract lives in the phase status doc's exit-criteria row; this
file carries the build notes and the Done record.)

## Test plan

- Story tests per the criteria row; real audio through the real
  transcriber where the story claims speech works; the demo is the
  closeout's proof; full suite green at ship.

## Done

Shipped: the one-call-site helper (capture → browser-side 16 kHz WAV →
the route), the hold-to-talk MicButton with honest states, mics on the
rail Ask + the in-world editor + the zone rename, and the no-mic lock
re-scoped to its true intent (the orb never touches the browser mic —
now locked BOTH ways). THE REAL PROOF: the fixture wav played as the
browser microphone and the REAL local Whisper filled the ask input with
"The quick brown fox jumps over the lazy dog." — no confirm step. See
[evidence-story-02.md](./evidence-story-02.md).
