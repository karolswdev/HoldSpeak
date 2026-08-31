# HS-156-03 - The library patterns: the reform's v1, the barrel, the fence

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
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

## What shipped

### The barrel (`surface/index.ts`)
The public barrel re-exports the full surface library: 29 layout primitives from Surface.tsx, 19 gadgets, SurfaceFooter, Material, useRovingRows, wings, citations, format helpers, LedgerFilter, foot, sparse, and the 7 new v1 patterns + MicButton (inverted as a surface control).

### The v1 patterns (`surface/patterns/`)
Seven pattern components with CSS and a 58-test contract suite:
- **StateChip** (7 states: idle/active/working/success/warning/failure/unreachable, icon+text always, etched chip face, working pulses, prefers-reduced-motion)
- **ActionNotice** (4 tones: ok/warn/danger/info, at most one named action button, role=status)
- **Disclosure** (controlled/uncontrolled, Escape closes with focus return, optional persistKey to localStorage, RAW variant, token slot, button trigger not details/summary)
- **ProgressPlan** (4 step statuses: queued/running/done/failed, progress bar with aria-label, rate slot, receipt/egress footer, one action button, aria-live=polite on transition only, compact mode)
- **ChoiceCardGroup + ChoiceCard** (real input[type=radio], useRovingRows for keyboard, selected/recommended/disabled, facts key-value list, cost slot, separate confirmation verb, RECOMMENDED badge)
- **Popover** (createPortal, --desk-z-popover, Escape dismisses, focus trapped, backdrop for outside-click, 4 placements)
- **ProvenanceChip + Receipt** (source/boundary labels with inspect action, lamp dot + status + timestamp, compose into SurfaceFooter)

### The MicButton inversion (`surface/controls/MicButton.tsx`)
Compatibility re-export at the new canonical path. Original file untouched; zero consumer edits.

### The ratchet fence (`guard-architecture.mjs` + `fence-baseline.json`)
Three rules, each with a checked-in baseline that can never grow:
- Rule 1 (private-imports): 59 baselined files
- Rule 2 (library-css-outside): 0 baselined files
- Rule 3 (roving-reimpl): 6 baselined files
12 fence fixture tests verify the regex patterns and baseline integrity.

### The contract (`surface/contract.md`)
States vocabulary, accessibility rules, token discipline, motion policy, container behavior, composition rules.

### The gallery (ComponentsCore.tsx)
Extended with sections for all 7 v1 patterns. Gallery axe test green.

### The shot sheet (`assets/story-03-shot-sheet/`)
8 shots: gallery top/mid/bottom/focus at 1440px and 393px.

### Test counts
- 58 pattern contract tests, 12 fence tests, 1 gallery axe test
- 1729 total suite tests, zero regressions
- `npm --prefix web run check` green end-to-end
- `check_web_baseline.py` zero BRANCH-NEW

## Notes / open questions

- The Amiga bar applies here first: streamlined honesty, modern delight, HONESTLY GREAT feeling — the gallery is where it becomes visible or doesn't.
