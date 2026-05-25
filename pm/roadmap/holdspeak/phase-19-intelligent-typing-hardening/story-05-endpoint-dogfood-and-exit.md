# HS-19-05 — Real Endpoint Dogfood and Phase Exit

- **Project:** holdspeak
- **Phase:** 19
- **Status:** done
- **Depends on:** HS-19-01, HS-19-02, HS-19-03, HS-19-04
- **Unblocks:** next intelligent-typing phase
- **Owner:** unassigned

## Problem

Fake-server tests prove the OpenAI-compatible contract, but daily-use hardening needs real endpoint evidence and a final phase summary.

## Scope

### In

- Manual or scripted smoke against one real local/LAN OpenAI-compatible endpoint.
- Known-good config notes.
- Final summary and phase closeout.
- Broad regression baseline.

### Out

- Benchmarking every endpoint family.
- Hosted service certification.

## Acceptance Criteria

- [x] At least one real endpoint smoke test is recorded or explicitly deferred with reason.
- [x] Known-good endpoint config is documented.
- [x] `final-summary.md` exists and follows roadmap-builder requirements.
- [x] Parent roadmap marks HS-19 done only after evidence and summary exist.

## Test Plan

- Focused endpoint smoke where environment allows.
- Broad non-metal pytest baseline.
- Web build.
- Markdown link sanity check.

## Notes

- 2026-05-24 closeout: local endpoint dogfood used `http://127.0.0.1:8080/v1` with model `Qwen3.5-9B-UD-Q6_K_XL.gguf`; see [evidence-story-05.md](./evidence-story-05.md).
- The environment needed the optional `openai` package installed into the venv before HoldSpeak's OpenAI-compatible runtime could load.
