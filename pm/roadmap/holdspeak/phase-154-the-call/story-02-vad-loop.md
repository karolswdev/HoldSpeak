# HS-154-02 - The ear: the energy VAD in a hands-free utterance loop

- **Project:** holdspeak
- **Phase:** 154
- **Status:** backlog
- **Depends on:** HS-153-06
- **Unblocks:** HS-154-03, HS-154-05
- **Owner:** unassigned

## Problem

The desk already hears (energy VAD → mic session → transcribe); the
Call needs that ear looped: utterance in, text out, sent as a normal
turn — nothing bypassing admission (settled design D2).

## Scope

- **In:** a `callLoop` module over the EXISTING pieces
  (`web/src/lib/vad.ts`, `micSession.ts`, `/api/dictation/transcribe`):
  while listening, endpoint detection closes the utterance, transcribes,
  and submits through the SAME composer send path (`start_turn` — the
  palette, guardrails, fence all apply). Silence/empty transcripts are
  dropped, not sent. Mic errors surface as the existing in-flow error
  row, never overlapping UI.
- **Out:** Silero VAD (recorded later), wake words, the call chip (03).

## Acceptance criteria

- [ ] vitest: a synthetic utterance (mocked micSession events) yields exactly one composer submit with the transcript; an empty transcript yields none; stopping the loop closes the mic session.
- [ ] The submit path is the composer's own send (spy on it) — no parallel turn entrance.
- [ ] Glass: with a stubbed transcribe route, the loop drives a visible turn at 1440 + 393.

## Test plan

- **Unit:** vitest `callLoop.test.ts`; a route test only if the transcribe route needs a tweak (prefer none).
- **Integration:** glass leg `call-loop`.
- **Manual / device:** story 05 (the attended voice leg is the owner's).

## Notes / open questions

- Click-to-toggle mic law holds (no push-to-talk).
