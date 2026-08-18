# HS-140-06 — The cold walk

- **Project:** holdspeak
- **Phase:** 140
- **Status:** backlog
- **Depends on:** 140-05
- **Unblocks:** phase close
- **Owner:** orchestrator owns walk and sitting; Terra counsel is read-only

## Problem

Component tests cannot prove that a person sees one obvious product and then a
useful furnished one. The phase needs a clean-install walk, real microphone and
transcription truth, the default pack, both widths, simple public wording, and
owner judgment before merge.

## Scope

- **In:** scripted fresh-HOME launch; happy path and failure legs at 1440×900
  and 393×900; screenshots, console/overflow checks; Copy/Keep/find-note proof;
  default-pack edit/grounding proof; reload persistence; entry-point docs lead
  with first value and accurately describe automatic furnished defaults; fresh
  Terra counsel; owner screenshot sitting.
- **Out:** CI monitoring, synthetic-only captures, prewritten evidence,
  unrelated documentation cleanup.

## Acceptance criteria

- [ ] Fresh HOME reaches one primary Dictate one sentence action with no setup
  prerequisite or competing product nouns above fold.
- [ ] A real sentence completes dictate→edit→Copy and dictate→edit→Keep→find.
- [ ] First reveal contains all six drawers, starter notes, and Everyday
  context; no separate Seed the desk action is required and no fake configured
  Agent/model appears.
- [ ] Edit a context note, explicitly attach Everyday context in Ask and an
  Agent, and prove the hydration uses the edit without setup vocabulary.
- [ ] Permission-denied, no-speech, unavailable-transcription, and seed-failure
  legs each show one truthful in-place recovery.
- [ ] Continue later and completion survive hub/browser restart.
- [ ] Both widths have zero horizontal overflow and zero console errors.
- [ ] README, Getting Started, and User Guide lead with the simple loop and
  describe the furnished defaults without stale explicit-seed instructions.
- [ ] Fresh Terra counsel has no blocker.
- [ ] Owner sees final both-width screenshots before merge.

## Test plan

- **Local gates:** focused Python setup/seed/grounding tests, focused Desk web
  tests, production build, doc drift guards, `git diff --check`.
- **Walk:** isolated temporary HOME, real bundled app/hub, both widths. Record
  commands/results only after they run.

## Notes

GitHub Actions is explicitly not watched or used as a phase gate.
