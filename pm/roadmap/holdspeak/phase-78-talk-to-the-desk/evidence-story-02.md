# Evidence — HS-78-02 — Speak-to-fill on every desk input

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-78-talk-to-the-desk`)

## What changed

- **The shared helper** (`web/src/scripts/speak-to-fill.js`) — the ONE
  `getUserMedia` call site for speech: a Web Audio tap gathers Float32
  frames, resamples to 16 kHz, builds the WAV in the browser, and POSTs
  the route. Hold to talk, release to fill, no confirm step (the owner's
  steer, verbatim in the header).
- **`MicButton`** (desk component): press-and-hold grammar with honest
  states (listening pulse / busy / a brief failed); it stops on
  pointer-leave; drag/click never bleed into the world (propagation
  stopped).
- **On every desk input**: the rail's Ask, the in-world editor (fills
  the kind's primary field: a note's body, a KB's name, an agent's
  system prompt), and the zone rename.
- **The desk no-mic lock re-scoped honestly** (its intent was always the
  ORB): meeting recording stays on the hub — the orb may never reference
  the browser mic or the helper (locked); desk components may import the
  helper but never call `getUserMedia` directly (locked); the reasoning
  is in the test's docstring.

## Verification artifacts — THE REAL THING

One Playwright session with the fixture wav playing AS the browser
microphone (`--use-file-for-fake-audio-capture`), the REAL local Whisper
(base) behind the route:

- Held the rail mic (the listening pulse asserted), the fixture sentence
  "spoke", released — and the input filled with **"The quick brown fox
  jumps over the lazy dog. The quick brown fox jumps."** No confirm
  step. (`02-spoken-into-the-ask.png`.)
- That one assertion covers the ENTIRE chain: getUserMedia → the tap →
  the browser-side resample/WAV → the route's strict decode → the real
  transcriber → the punctuation pass → the fill.
- vitest 9/9; the re-scoped locks 5/5; web build green. Two guards fired
  on the full sweep and were fixed honestly: my own comment name-dropped
  the banned call (the P73 lesson repeating — reworded) and the manifest
  gained the helper's call site (regenerated). Full suite at ship:
  **3100 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] Every desk text input carries the mic; hold-talk-release-fill; no
      confirm step.
- [x] Real speech through the real pipeline, asserted on the filled
      input.
- [x] The orb's hub-recorder rule survives, stronger than before.
