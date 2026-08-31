# HS-156-08 - The beauty pass: the selector learns imagination

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
- **Depends on:** HS-156-07
- **Unblocks:** -
- **Owner:** unassigned

## Problem

The OWNER, on reviewing the close (2026-08-31, verbatim): "I don't
fully agree with a final closure... The profile selector is the
biggest culprit, unimaginative huge walls of texts, not really divided
by anything, forcing the user to select between that. Super
disappointed." The functional gates passed; the imagination gate did
not. The standing ruling applies: beauty pass after every functional
pass, and THE OWNER SEES SHOTS BEFORE MERGE.

## The culprit surfaces (walk them first, at 1440 and 393)

1. **The pack cards** (story-05 shots): seven near-identical mono
   lines per card, three cards stacked = a wall. Nothing is grouped,
   weighted, or summarized; the eye has no anchor.
2. **The assignments editor / profile candidate picker** (the advanced
   layer): raw candidate rows, same disease.
3. Any surface that presents "pick a profile/model" as an undivided
   list.

## Design direction (bind to the council + the Amiga star)

- A pack card is an OBJECT, not a list: name + one-sentence character;
  ONE summary line ("6 jobs → your Qwen server on .43 · speech →
  Whisper small"); the per-job detail folded behind a Disclosure, not
  splattered; size/cost as a fact chip, RECOMMENDED as presence not
  just a corner tag. Visual differentiation BETWEEN tiers (weight,
  accent temperature, an emblem — deliberate, not decoration).
- Group per-job lines by what serves them, never one row per group id
  when five rows say the same thing.
- The candidate picker: profiles as material cards (name, boundary
  chip, what-it-serves, health) with hierarchy — never raw rows.
- Library-first: extend ChoiceCardGroup/StateChip/Disclosure contracts
  (slots for summary/emblem/fold) so EVERY room inherits the upgrade;
  the ratchet fence stays law. Gallery states + shot sheet updated.
- The bar: Amiga's streamlined honesty + modern delight. If a screen
  reads as a wall of text, it fails regardless of tests.

## Acceptance criteria

- [x] The pack cards and the candidate picker redesigned per the direction; before/after shot sheet at 1440 + 393; the ORCHESTRATOR's gate looks, then THE OWNER SEES THE SHOTS and his verdict is the gate.
- [x] Zero new one-off furniture (fence holds); contract tests updated with the extended slots; `npm --prefix web run check` green; baseline zero branch-new.
- [x] The stopwatch rig still passes (beauty must not cost the minute).

## Test plan

- **Unit:** extended pattern contract suites; frontDoor/editor vitest.
- **Integration:** the 156 glass file re-shot.
- **Manual / device:** the owner's verdict on the shots — the only close.
