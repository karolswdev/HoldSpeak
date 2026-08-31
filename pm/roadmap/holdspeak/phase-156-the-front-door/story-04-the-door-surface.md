# HS-156-04 - The door surface: pack cards, the health strip, the advanced fold

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
- **Depends on:** HS-156-01, HS-156-02, HS-156-03
- **Unblocks:** HS-156-05, HS-156-06, HS-156-07
- **Owner:** unassigned

## Problem

Settings → Models must open on a door, not an engine room: three pack
cards and one confirmation when unconfigured; a one-line health strip
with the whole advanced layer folded underneath once configured
(settled design D3; the owner's B: "easy to then go in and dig").

## Scope

- **In (council law):** built FROM the 03 library patterns — the cards are `ChoiceCardGroup`, the plan is `ProgressPlan`, the strip is an `ActionNotice`, the fold is `Disclosure`; zero new one-off furniture (the fence enforces it). The door view inside the existing Models settings surface:
  when any group is unassigned → pack cards (name, one line per job,
  total download size, Balanced marked recommended) + "Set up my own"
  (jumps to the advanced layer); confirm → the live plan view (per-item
  progress from 02, in-flow, no modal); done → the health strip
  ("Everything wired · Balanced · change") above the UNCHANGED advanced
  Library/Assignments view. Every attention state anywhere on the
  Models surface names ONE next action and carries its button. Desk
  tokens, keyboard reachable, 393-safe.
- **Out:** wording overhaul beyond the door path (04), removing any
  advanced capability (forbidden).

## Acceptance criteria

- [ ] vitest: unconfigured state renders the cards (complete per-job lines, sizes); confirm posts apply and renders the live plan; configured state renders the strip + the advanced fold opens; an attention state renders exactly one action button.
- [ ] Glass 1440 + 393 on a real hub: fresh desk → cards; apply a stub pack → plan progresses to wired → strip appears; the advanced fold still exposes Library + Assignments fully; zero overflow. Shots both widths.
- [ ] Zero features removed from the advanced layer (the existing Library/Assignments vitest suites still pass untouched).

## Test plan

- **Unit:** vitest `frontDoor.test.tsx`.
- **Integration:** glass legs `door-cards`, `door-apply`, `door-strip` in `tests/e2e/test_hs156_front_door_glass.py`.
- **Manual / device:** story 07.

## What shipped

Settings → Models is now the front door.

**FrontDoorView** (`web/src/pages/cores/frontDoor.tsx`, 310 lines) replaces
the bare ModelLibraryCore in the Models module slot. Three phases:

1. **Cards** (unconfigured): `ChoiceCardGroup` renders up to three pack
   cards (Light, Balanced, Full) from `GET /api/front-door/recommendation`.
   Each card shows all per-job display lines (7 assignment groups + speech
   + TTS), the total download size, and the RECOMMENDED badge on Balanced.
   A "Set up my own" action opens the advanced layer inline. The "Set up"
   confirm button fires `POST /api/front-door/apply`.

2. **Plan** (applying or failed): `ProgressPlan` renders each apply-plan
   item with its live status. Polls `GET /api/front-door/apply` every 1.5 s
   for per-item progress. A failed plan shows a "Resume" action that
   re-posts the same pack.

3. **Strip** (configured): `ActionNotice` shows "Everything wired" (ok tone)
   or the first attention row with its repair text + a single "Fix" button
   (warn tone). Below it, a `Disclosure` fold labeled "Advanced" opens the
   unchanged `ModelLibraryCore` + `CapabilityAssignmentsCore` — zero
   features removed from the advanced layer.

Council law honored: cards = ChoiceCardGroup, plan = ProgressPlan,
strip = ActionNotice, fold = Disclosure. Zero new one-off furniture.
All imports via the surface barrel (`web/src/desk/surface/index.ts`).
Architecture fence passed (563 files, zero framework residue).

**Files:**
- `web/src/pages/cores/frontDoor.tsx` — the door component
- `web/src/pages/cores/frontDoor.css` — minimal layout CSS
- `web/src/pages/cores/settingsModels.tsx` — rewired from ModelLibraryCore to FrontDoorView
- `web/src/pages/cores/__tests__/frontDoor.test.tsx` — 6 vitest tests
- `tests/e2e/test_hs156_front_door_glass.py` — 3 glass legs (door-cards, door-apply, door-strip)
- `assets/story-04-shots/` — 12 screenshots (1440 + 393) + index.md

## Notes / open questions

- The door lives IN the Models surface — no new room, no wizard modal (no-modals law).
- "Needs attention" inside the Library is the Library's own summary (untouched
  advanced layer); the door's ActionNotice replaces it at the surface level.
- Wording refinement (the "Thoughts & notes Fix" repair text) lands in story 05
  (the jargon purge).
