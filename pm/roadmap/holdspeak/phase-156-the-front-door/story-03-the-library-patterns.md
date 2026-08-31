# HS-156-03 - The library patterns: the reform's v1, the barrel, the fence

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-156-04, HS-156-06, HS-156-07
- **Owner:** unassigned

## Problem

The council ruled (assets/design-council.md, both voices converging):
the front door must not mint more one-off furniture. The library's v1
patterns, the public barrel, and the ratchet fence land BEFORE the door
surface and topology build — the first customer proves the contract.

## Scope

- **In:** `surface/index.ts` (the public barrel — the only supported
  feature import path) + `surface/contract.md` (the component law:
  states, a11y, tokens, motion, container behavior, examples). The v1
  patterns under `surface/patterns/`, each with contract tests and the
  closed vocabularies from the codex memo: `StateChip`, `ActionNotice`
  (ONE named next action), `Disclosure` (RAW/advanced fold, focus
  return, Esc, optional persistence), `ProgressPlan` (stable step ids,
  queued|running|done|failed, byte progress, receipt/egress slots, one
  resume action), `ChoiceCardGroup` (real radio semantics, recommended
  state, separate confirmation verb), `Popover` (in-flow, anchored,
  focus law), promoted `ProvenanceChip`/`Receipt` composing into the
  existing SurfaceFooter law. Fix the MicButton dependency inversion
  (moves inward as a control; compatibility re-export). The RATCHET
  FENCE in guard-architecture.mjs: a checked-in baseline of legacy
  violations that can never grow (barrel-only imports for new code; no
  feature CSS restyling library-owned states/chips/folds/plans; no
  reimplemented roving). The gallery: deterministic named states for
  every v1 pattern at 1440 + 393, captured as the story's SHOT SHEET
  (the first first-class visual gate).
- **Out:** `TopologySurface` (lands as the topology story's first
  act), migrating existing rooms (the ratchet handles them over time),
  the desk-tokens.css shim retirement (a plain-words checklist item).

## Acceptance criteria

- [ ] Every v1 pattern has contract tests (states, keyboard, a11y roles, token compliance) and renders its gallery states; the shot sheet (1440 + 393, all states, keyboard focus visible) ships in evidence and is LOOKED AT — reviewer + verdict recorded.
- [ ] The fence: guard-architecture.mjs rejects a fixture violation of each new rule; the legacy baseline is checked in and a test proves it cannot grow.
- [ ] The barrel is complete for the v1 surface; a new-code import of a private surface path fails the guard.
- [ ] `npm --prefix web run check` green end-to-end; zero regressions in the existing surface/gadgets suites.

## Test plan

- **Unit:** vitest contract suites per pattern; the fence fixtures.
- **Integration:** the gallery render (glass or vitest-DOM) producing the shot sheet.
- **Manual / device:** the shot-sheet review is the gate (orchestrator's eyes; the owner sees it in the phase exhibit).

## Notes / open questions

- The Amiga bar applies here first: streamlined honesty, modern delight, HONESTLY GREAT feeling — the gallery is where it becomes visible or doesn't.
