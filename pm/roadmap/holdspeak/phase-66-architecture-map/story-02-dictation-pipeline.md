# HS-66-02 — The dictation pipeline, diagrammed

- **Project:** holdspeak
- **Phase:** 66
- **Status:** backlog
- **Depends on:** HS-66-01
- **Unblocks:** HS-66-04
- **Owner:** unassigned

## Problem
The dictation path (entry, capture, transcribe, the optional pipeline
stages, type, and the learning loop) is the product's core and is
undocumented as a flow.

## Scope
- **In:** Mermaid diagrams in `docs/ARCHITECTURE.md` for: the end-to-end
  dictation flow (hotkey AND wake-word entry with the preview default,
  capture, transcribe, the pipeline stages — intent route, project
  context, target profile, LLM rewrite — and typing); the
  journal/correct/replay learning loop; voice-command dispatch; the
  device/ESP path into voice typing and agent reply. Prose names the real
  modules. Conditional/opt-in paths shown as such.
- **Out:** the meeting side (HS-66-03).

## Acceptance criteria
- [ ] Each diagram traced against shipped code (module names current
      post-decomposition); opt-in paths marked.
- [ ] All blocks render (guard green); voice guard + full suite green.

## Test plan
- The render guard; the full suite.
