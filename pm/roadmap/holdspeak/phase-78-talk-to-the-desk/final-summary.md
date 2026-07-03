# Phase 78 — Talk to the Desk: final summary

- **Closed:** 2026-07-02/03 — **4/4 stories**, opened on the owner's video
  review and closed the same night.
- **Branch:** `phase-78-talk-to-the-desk` (merged to `main` by PR).

## What shipped, in one paragraph

The web desk is talked to now. The hub gained its first transcribe route
(`POST /api/dictation/transcribe`: one strict WAV shape, the runtime's own
local Whisper, the dictation punctuation pass, no persistence, no egress,
honest refusals); every desk input carries a hold-to-talk mic (the shared
browser-capture helper is the ONE mic call site; the orb's hub-recorder
rule survived the re-scope stronger, locked both ways); and the marquee
moment is real — a waiting Claude's question stands on the desk (a latent
mapper bug had kept the question invisible; fixed) and holding the mic
answers it through the existing HSM-13 inject seam. No confirm steps
anywhere.

## Proven with REAL speech

The fixture recording played as the browser microphone and the REAL local
Whisper (base) ran behind the route in every proof: the ask input filled
with "The quick brown fox jumps over the lazy dog."; the coder's answer
reached the remote seam targeted at `agent`; the closeout demo recorded
all of it (the waiting Claude answered by voice, a note spoken into
existence, the filing fix on camera, the Owl's real `.43` answer landing
as an artifact).

## The numbers

Suite **3100 passed, 37 skipped** at close (+5 this phase); vitest 9/9;
every fired guard updated honestly (the manifest twice; my own comment
tripping the mic lock — the P73 lesson repeating).

## Recorded gotchas

- A session's awaiting flag derives from the TRANSCRIPT file under
  `capture_messages`, not from any payload message; the question's wire
  key is `last_assistant_text`.
- The demo's intent-router could not reach the LAN endpoint from the
  harness and degraded gracefully (delivery still happened) — the
  designed posture, visible in the logs.
