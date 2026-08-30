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
| HS-154-01 | The voice (browser default, kokoro-onnx extra, /api/tts) | done | [story-01-tts-route](./story-01-tts-route.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-154-02 | The ear (energy VAD hands-free loop) | done | [story-02-vad-loop](./story-02-vad-loop.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-154-03 | Call mode (threads.call_mode, chip, frame — M9) | backlog | [story-03-call-mode](./story-03-call-mode.md) | - |
| HS-154-04 | Speaker glyph + auto-speak (S6 chunks, barge-in) | backlog | [story-04-speaker-glyph](./story-04-speaker-glyph.md) | - |
| HS-154-05 | The walk and the close | backlog | [story-05-walk-and-close](./story-05-walk-and-close.md) | - |

## Where we are

HS-154-01 (the voice) delivered: the ONE client TTS seam (`tts.ts`), the
server route family (`/api/tts/status`, `/api/tts`, `/api/tts/download`),
the `holdspeak[tts]` optional extra in pyproject.toml, and the Settings
TTS block in the Sounds module. 10 python tests + 9 vitest + 2 glass
(1440+393 zero overflow) pass. API surface regenerated (564 routes, +3).
Web baseline zero BRANCH-NEW. Evidence captured.

HS-154-02 (the ear) delivered: `callLoop.ts` (the hands-free utterance
loop state machine over the existing energy VAD, mic session, WAV encoder,
and transcribe route) + `callLoopWiring.ts` (binds onSubmit to the
composer's own `sendTurn` -- no parallel turn entrance). 11 vitest
(callLoop) + 5 vitest (wiring) + 1 glass (call-loop turn visible at
1440+393, zero overflow) pass. Web baseline zero BRANCH-NEW (1608 passed).
Evidence captured. Next: story 03 (call mode).

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
