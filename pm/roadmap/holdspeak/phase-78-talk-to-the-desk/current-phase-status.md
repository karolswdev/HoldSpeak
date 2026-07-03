# Phase 78 — Talk to the Desk

**Status:** **CLOSED — 4/4 (2026-07-02/03).** See [final-summary.md](./final-summary.md).
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
| HS-78-02 | Speak-to-fill on every desk input | HIGH | **done** (hold-to-talk mics on ask/editor/rename; the REAL proof: the fixture spoke as the browser mic and real Whisper filled the input; the orb lock re-scoped + strengthened; see [evidence](./evidence-story-02.md)) | 01 |
| HS-78-03 | Talk to the waiting coder | HIGH | **done** (Hold to answer → select + the HSM-13 inject; the question-never-rendered bug fixed; the REAL marquee proof; see [evidence](./evidence-story-03.md)) | 01 |
| HS-78-04 | The re-recorded demo + docs + closeout | MED | **done** (5 beats on camera: the marquee first, no staged friction; docs speak the mic; see [evidence](./evidence-story-04.md)) | 01–03 |

## Exit criteria

- [x] `POST /api/dictation/transcribe` accepts browser-captured 16 kHz
      mono PCM (a size cap; loopback/token posture unchanged), runs the
      runtime's OWN transcriber (the one model, the one lock), and
      returns `{text}`; audio is never persisted; nothing egresses
      (HS-78-01).
- [x] Every desk text input (the rail Ask, the note editor's fields, the
      zone rename) carries a speak-to-fill mic: press, talk, release,
      the text lands in the field — no confirm step (HS-78-02 — proven
      with real speech through the real transcriber).
- [x] The coder pull-out's answer is spoken: mic → transcribe → inject
      through the existing `/api/dictation/remote` seam; proven against
      a seeded waiting session (HS-78-03 — plus the latent
      question-never-rendered bug fixed).
- [x] The demo re-records with every lane seeded (the waiting coder
      included) and the voice fills on camera; docs speak the mic;
      guards green; PR merged on a conclusion-checked green (HS-78-04).

## Where we are

**2026-07-03 — PHASE CLOSED (4/4).** The desk is talked to. The demo
shows all three review answers on camera: the waiting Claude answered by
voice first, the spoken note leaving the stage when filed, and no staged
confirm friction anywhere. Real speech, real Whisper, the real inject
seam, the real .43 answer.

**2026-07-02 — HS-78-03 done (3/4).** The marquee moment is real: a
waiting Claude's question stands on the desk (a latent mapper bug had
kept it invisible — fixed) and holding the mic answers it, real speech
through real Whisper into the real inject seam. One story left: the
re-recorded demo.

**2026-07-02 — HS-78-02 done (2/4).** You can talk to the desk. Real
recorded speech, played as the browser microphone, rode the whole chain
(capture → browser-side WAV → the strict route → the REAL local Whisper
→ the punctuation pass) and landed in the rail's ask input with no
confirm step. The mics sit on every desk input; the orb's hub-recorder
rule is locked both ways. Next: the coder (03), the demo (04).

**2026-07-02 — HS-78-01 done (1/4).** The hub can hear the browser: the
strict WAV route runs the runtime's own transcriber with the dictation
punctuation pass, honest refusals, no persistence, no egress. Next: the
mics (02) and the coder (03).

**2026-07-02 — scaffolded (0/4).**
