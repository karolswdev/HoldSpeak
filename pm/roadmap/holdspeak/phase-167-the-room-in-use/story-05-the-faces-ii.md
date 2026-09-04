# HS-167-05 - The faces recomposed II: Review, Update, Steward — and the beauty pass

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
- **Depends on:** HS-167-02, HS-167-03, HS-167-04
- **Unblocks:** HS-167-06
- **Owner:** unassigned

## Problem

The three postures (765 + 497 + 618 lines) hand-roll their row
internals, comparison layout and the whole policy form; the
cadence is read-only on the steward face; the enrichment count has
nowhere to land. And the arc never had a whole-Room beauty pass —
every phase's beauty was judged alone.

## Scope

- **In:** ReviewPosture.tsx (comparison on the split species; kind
  groups and source chips on the chip vocabulary), UpdatePosture.tsx
  (document view + sources + list rows on the ledger grammar),
  StewardPosture.tsx (step rows with receipt refs, run list, circuit
  rows, the policy sheet on GadgetGroup with the cadence as an
  edit-in-world gadget wired to 02's savePolicy; the enrichment
  count on the OBSERVE step's Receipt) — all to the mockups, barrel
  only. Then THE BEAUTY PASS over all eight faces together: the
  Workbench 2.0 mold's iconography from the ratified palette, hover/
  pressed states, spacing rhythm, the one accent — the faces read as
  one Room. Shots at both widths through the rebuilt rigs (160, 162,
  163, 164, 166) plus a stitched "the whole Room" sheet: all eight
  faces side by side at 1440, for the owner's eye (the 156-08
  precedent: before/after, both widths; a flinch = redo).
- **Out:** the walk (06); new behavior beyond the 02 wires.

## Acceptance criteria

- [x] Every hand-rolled block the 01 audit named in these files is gone; dead CSS deleted; the cadence edits through the face and the change is visible on the next tick's schedule.
- [x] The 160/162/163/164/166 glass rigs pass with unchanged assertions; web baseline zero branch-new.
- [x] The whole-Room sheet + before/after pairs in the gallery; the owner's shot verdict recorded verbatim (PASS required before 06's attended walk).

## Landed — the functional pass (2026-09-03)

Four orchestrator rounds on the three postures (the whole-Room beauty
pass is the SEPARATE second half of this story, brief next). Review:
the full-width queue on room ledgers, the row expanding in flow into
CURRENT | PROPOSED SurfaceFacts, chips, the id a quiet mono token,
the verbs + keyboard grammar kept, the conflict's hashes in a closed
Disclosure (the wall gone). Update: DRAFTS ledger, the editor with
the mic in its toolbar, the SOURCES ledger, an ActionNotice for the
unverified claim, the footer's honest egress chip + Save · Regenerate
· Copy · Publish. Steward: THE RUN as the six-phase ProgressPlan with
counts only (`1 source`, `6 effects`), the receipt line `RUN N ·
COMPLETED · 6 PHASES` (the eleven-COMPLETED-rows scar paid), the RUNS
and CIRCUITS room ledgers (glyph lead, the StateChip in cells), the
circuit ActionNotice in tokens, POLICY as GadgetRows with
StepperGadgets (the cadence stepper WIRED to 02's write), the grant
as tokens (`UNATTENDED OFF` when off). ORCHESTRATOR CATCHES: the
worker's round-4 shots were pixel-identical to round 3 — a BUILD
RACE: two hashed ProjectMemoryCore chunks coexisted under the
bundle and index.html was newer than chunks that predated the edits,
so `_ensure_build` trusted a stale bundle; the helper now compares
the OLDEST built chunk against the newest source and never touches
the marker (rebuilt, verified by grepping the chunk for the new
strings before re-shooting). A `z-index: 1` literal caught by the
token gate → `--desk-z-local`. Beauty-pass ledger: token rows (the
grant, the receipt refs) render as bare uppercase word runs without
chip geometry, and the run's receipt refs include phase names (effects
only); the ASSESSMENT cell on Review rows; plus 04's three (MetricStrip
wrap, stream entry density, the interview's disabled Next). Gates read
by the orchestrator: project-room vitest 537/537; baseline zero
branch-new; token gate clean; glass 160/162/163/164 26 passed; 51
fresh after-shots harvested from the honest bundle.

## Landed — the beauty pass (2026-09-03)

Over all eight faces, two rounds: token rows and receipt refs with
chip geometry (a `data-chip` variant on `surface-token` in the
barrel; effects only on the run's refs), MetricStrip `dense` (one
row at 640, 2×2 at 393), SurfaceStream `dense` (12px mono entries in
the Room), the interview's Next primary present-disabled while the
answer is empty, the proposed watches (SetupBrief) as a room ledger
with provider emblems + cadence/action/provenance cells + a StateChip
trailing, TestResult as receipt tokens + a ledger of matches (the
last sentence gone), the mold made consistent (emblems, hover/open
wells, one accent per footer, 10px section labels, ScrollHint on
every scrolling well, no ellipsized identity at 393). Sheets:
story-05-shots/beauty/whole-room-1440.png + whole-room-393.png (the
eight faces side by side) + 98 after-shots. Gates read by the
orchestrator: vitest 789/789; baseline zero branch-new; token gate
clean; all eight glass rigs 46 passed + 1 honest skip. The live
runner's glass assertions (tests/e2e/live167_walk.py) pass on the real
DOM at both widths. **THE OWNER'S SHOT VERDICT (2026-09-03), verbatim: "PASS"** — on the
gallery https://claude.ai/code/artifact/3d5a2a6a-d1b6-4a21-ad73-3c8c09417a6b
(the two whole-Room sheets + ten before/after pairs).

## Test plan

- **Web + glass:** as 04, over the posture rigs.
- **Eye:** the gallery artifact republished; the orchestrator reads every PNG against the mockups first.
