# Phase 154 - The Desk Chat — The Call (DC-04)

**Last updated:** 2026-08-30.

## Goal

The Thread learns to talk and listen: browser-default TTS with a
kokoro-onnx opt-in extra, the existing ear looped hands-free, one
visible call state the owner can always stop (settled design D1–D5;
counsel M9/S6/R4; the TTS feasibility ruling supersedes RFC §6.8-B).

## Scope

- **In:** the five stories below; the charter lands on PR #511
  (`feat/deskos-platform-revolution`), the superseding merge vehicle.
- **Out:** Silero VAD, voice cloning, wake words, the Crew (155).

## Exit criteria (evidence required)

- [ ] All five stories done with evidence; glass 1440+393; metal on `.43`; close counsel zero open must-fix; sweep name-diff clean vs main.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-154-01 | The voice (browser default, kokoro-onnx extra, /api/tts) | backlog | [story-01-tts-route](./story-01-tts-route.md) | - |
| HS-154-02 | The ear (energy VAD hands-free loop) | backlog | [story-02-vad-loop](./story-02-vad-loop.md) | - |
| HS-154-03 | Call mode (threads.call_mode, chip, frame — M9) | backlog | [story-03-call-mode](./story-03-call-mode.md) | - |
| HS-154-04 | Speaker glyph + auto-speak (S6 chunks, barge-in) | backlog | [story-04-speaker-glyph](./story-04-speaker-glyph.md) | - |
| HS-154-05 | The walk and the close | backlog | [story-05-walk-and-close](./story-05-walk-and-close.md) | - |

## Where we are

Chartered 2026-08-30 from the settled design (assets/settled-design.md)
on the superseding merge vehicle (PR #511). Building starts once #511's
own CI settles; the port is already proven on its head (178 python +
77 vitest).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Web Speech voices vary by browser/OS | medium | the seam picks the best local voice; the R4 fallback law | an utterance with no audible output on the owner's hub |
| kokoro-onnx GPL chain surprises | low | opt-in extra, visible note, lazy import | GPL code imported in the base install |

## Decisions made (this phase)

- 2026-08-30 - TTS default = browser Web Speech; kokoro-onnx = opt-in extra with a GPL note - licence + Python 3.13 feasibility - orchestrator ruling (supersedes RFC §6.8-B).
- 2026-08-30 - The charter lands on PR #511, not #507 - vehicle superseded - owner ruling.

## Decisions deferred

- Silero VAD - trigger: the energy VAD misfires on the owner's real hub - default keeps the energy VAD.
