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

- [x] All five stories done with evidence; glass 1440+393; metal on `.43`; close counsel zero open must-fix (M1+S1–S4 fixed in-round); sweep name-diff clean vs main.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-154-01 | The voice (browser default, kokoro-onnx extra, /api/tts) | done | [story-01-tts-route](./story-01-tts-route.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-154-02 | The ear (energy VAD hands-free loop) | done | [story-02-vad-loop](./story-02-vad-loop.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-154-03 | Call mode (threads.call_mode, chip, frame — M9) | done | [story-03-call-mode](./story-03-call-mode.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-154-04 | Speaker glyph + auto-speak (S6 chunks, barge-in) | done | [story-04-speaker-glyph](./story-04-speaker-glyph.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-154-05 | The walk and the close | done | [story-05-walk-and-close](./story-05-walk-and-close.md) | [evidence-story-05](./evidence-story-05.md) |

## Where we are

Phase 154 COMPLETE 5/5. The walk (HS-154-05): metal DRY 5/5 + LIVE 5/5
on `.43` (call_mode law, thread_call_state frames on the bus, the TTS
404 law with zero egress receipts, the ear's server half — LIVE
honestly BLOCKED-BY-ENV, no Whisper on the isolated hub — and the
grammar override holding on a live Qwen turn); glass 5/5 both widths;
docs (README, USER_GUIDE, RFC §6.8 SHIPPED; MCP counts unchanged);
counsel RATIFY-W-C — M1 (the server voice escaped the stop click) +
S1–S4 all fixed in-round; sweep name-diff vs main@fb2d1082's 27 → the
schema-snapshot fence regenerated (call_mode) and one recorded
refinement-coordinator flake; web baseline zero branch-new. Exhibit:
https://claude.ai/code/artifact/bc5bb869-3817-4b96-8936-b128cdb1b7a3.
HOLDING for the owner's attended voice leg — it holds the merge word
on PR #513.

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
