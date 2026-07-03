# Phase 78 — Talk to the Desk

**Status:** open — scaffolded 2026-07-02 (0/4).
**Owner call that opened it:** the video review (2026-07-02): "why would
we need to confirm the dictation? That's totally not user friendly. We
need to be able to just talk to this stuff" + "I thought this demo would
also show claude waiting for an answer."

## Why

The web desk is typed at, not talked to: the rail's Ask and the note
editor are keyboard inputs on a voice product, violating the standing
voice-first rule the iPad already lives by (every input carries a
speak-to-fill mic). The root cause is structural: **the hub exposes no
transcribe route at all** (mic.js documents it), so nothing in the
browser can turn speech into text. And the marquee moment — a coder
session waiting and being answered — never appears in demos.

## The seams (verified before scaffolding)

- The runtime's Transcriber is callable from any thread (the P60 MLX
  pinning lives INSIDE `_MlxTranscriber`); `_ensure_transcriber_loaded`
  is the load path; `transcription_lock` serializes.
- `/api/dictation/remote` (HSM-13) already injects text into a waiting
  coder session — "talk to the coder" is two existing seams joined by
  one new route.
- Browser capture via the Web Audio API produces 16 kHz mono PCM without
  MediaRecorder's webm container (the hub decode stays trivial).

## Stories

| ID | Story | Sev | Status | Depends |
|---|---|---|---|---|
| HS-78-01 | The transcribe route (local Whisper, no egress) | HIGH | **done** (the runtime verb + seam + the strict WAV route; 5/5; see [evidence](./evidence-story-01.md)) | — |
| HS-78-02 | Speak-to-fill on every desk input | HIGH | todo | 01 |
| HS-78-03 | Talk to the waiting coder | HIGH | todo | 01 |
| HS-78-04 | The re-recorded demo + docs + closeout | MED | todo | 01–03 |

## Exit criteria

- [x] `POST /api/dictation/transcribe` accepts browser-captured 16 kHz
      mono PCM (a size cap; loopback/token posture unchanged), runs the
      runtime's OWN transcriber (the one model, the one lock), and
      returns `{text}`; audio is never persisted; nothing egresses
      (HS-78-01).
- [ ] Every desk text input (the rail Ask, the note editor's fields, the
      zone rename) carries a speak-to-fill mic: press, talk, release,
      the text lands in the field — no confirm step (HS-78-02).
- [ ] The coder pull-out's answer is spoken: mic → transcribe → inject
      through the existing `/api/dictation/remote` seam; proven against
      a seeded waiting session (HS-78-03).
- [ ] The demo re-records with every lane seeded (the waiting coder
      included) and the voice fills on camera; docs speak the mic;
      guards green; PR merged on a conclusion-checked green (HS-78-04).

## Where we are

**2026-07-02 — HS-78-01 done (1/4).** The hub can hear the browser: the
strict WAV route runs the runtime's own transcriber with the dictation
punctuation pass, honest refusals, no persistence, no egress. Next: the
mics (02) and the coder (03).

**2026-07-02 — scaffolded (0/4).**
