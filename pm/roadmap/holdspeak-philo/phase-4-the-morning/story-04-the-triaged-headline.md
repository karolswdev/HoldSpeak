# PHILO-4-04 - The triaged headline

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** backlog
- **Depends on:** PHILO-4-01 (the quiet branch it draws, boards 7b, 8a, 8b)
- **Unblocks:** the morning in one move
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** Astra r3 finding 6 (the PHILO-4-01 canvas check, round three)

## Problem

After every row is handled, the stored headline still says "N things waiting" with nothing to reach. The producer composes the headline once, at generation, from the brief's items (`holdspeak/services/monday_brief_service.py:327-387`; the items in their sections, e.g. `Commitment due` into `decisions` at `:812`). Triage writes the shelf and never rewrites the headline (`shelve`, `:1110-1139`). The Arrival's quiet branch renders that stored headline when nothing is untriaged (`web/src/desk/chair/ChairHome.tsx:1283`). So the generated snapshot and the current triage state are conflated: on the canvas board 7b the owner has triaged all four rows and reads `1 thing changed, 1 thing waiting, 2 decisions waiting.` (the real `_compose` output, `assets/story-01-canvas/harness/compose_headline.py`).

## Scope

- **In:** the result below, its fence(s) red pre-fix, the face at 1440 and 393.
- **Out:** everything the phase status lists as out; the brief window (`BriefView.tsx`).

## Acceptance criteria

- [ ] The headline distinguishes the generated snapshot from the current triage state, without rewriting historical counts (the stored headline and the items stay as generated).
- [ ] Canvas first: the face is designed on the library and the owner ratifies it before build (UX-CANON A.2).
- [ ] Fence red pre-fix: a brief with every row triaged renders a headline that names waiting items with nothing to reach.

## Effort (council-style estimate, not a promise)

0.5–1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the quiet branch on the rig at 1440 and 393, observations retained under this phase's assets.
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered (unratified) from Astra's round-three check of the PHILO-4-01 canvas (finding 6); the canvas README ask 6 points here.
