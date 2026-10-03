# PHILO-13-17 - C7 The phone desk

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** in-progress
- **Depends on:** PHILO-13-11 (C1 canvas ratified); this story's own canvas ratified
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C7 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/faces-surfaces.md` F4 (`:191`); `grounding/faces-jobs.md` F12 (`:178`); handover XXXII carried ledger (the Chair dock over the meeting preview at 393; G5)
- **Canvas:** one, on the C1 material, at 393 (the frame, one window at a time, the swipe)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

At 393 the frame takes at most a sixth of the screen; one window at a time, swiped.

## Problem

At 393 the menu bar (48 px, only Go; the clock wraps), the capture bar and a two- to three-row Dock (125–170 px) take 250–360 of 852 px; a window gets ~540–631 px (`grounding/faces-surfaces.md:67`, `:75`, `:79`; `grounding/faces-jobs.md:178`). The needs-you `Done` verb and the send well fall below the fold (`grounding/shots/jobs/J1-01-arrive-393.png`, `J2-04-preview-393.png`). The capture bar owns the hit points of the meeting preview's chips (`grounding/shots/surfaces/60-ledger-chair-meeting-preview-pop-393.png`; `grounding/faces-surfaces.md:160`). The Meetings footer chip runs under `MD`/`SRT` (G5, `63-ledger-chair-open-meeting-pop-393.png`). A second window covers the first with no visible point to tap (`41-frame-meetings-open-pop-393.png`, `43-frame-two-windows-pop-393.png`).

## Scope

- **In:** the canvas; Astra checks; the owner ratifies. The 393 frame (menu bar, Dock, capture bar) at most 852/6 ≈ 142 px together; one window at a time; a swipe between open windows; the capture bar never over content; G5 fixed; the menus Desk/Object/Window reachable at 393. Files: CSS, `DeskWindow.tsx` compact branch (`web/src/desk/components/DeskWindow.tsx:205`, `:737`), `window/*`, `web/src/desk/chair/**` (the capture bar).
- **Out:** the 1440 frame (C1); the iPad and Swift desks (the web Desk is the spec).

## Acceptance criteria

- [x] Canvas ratified by the owner (his word recorded) before the first face commit. **RATIFIED 2026-10-03: "Ratify, build it (Recommended)"** on the page https://claude.ai/artifact/EvmqHZkrnKGfxdQgAqNX7Y, after Astra p13-c57-canvas-check RATIFY-WITH-CONDITIONS (six conditions paid in round two, 3ed1ba43); all six recommended defaults stand.
- [ ] Window content ≥ 700 of 852 px at 393 on every walked surface (red on main: ~540–631).
- [ ] One window at a time; a touch swipe moves to the next open window and back.
- [ ] No chrome owns a content verb's hit point (`elementFromPoint` at each verb's centre and its 44 px band, touch); the capture-bar overlap and G5 are red on main, green here.
- [ ] The Desk, Object and Window menus are reachable at 393.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of its canvas (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the compact layout state; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** Playwright at 393×852 with `has_touch`, every press a tap, swipes as touch events; the hit-ownership probe of `grounding/faces-surfaces.md:13`.
- **Atlas:** the J1 and J2 phone cases at 393, one case per `scripts/graph_walk.py run` invocation; the 1440 runs of the same cases still pass.
- **Shots:** the Chair, a window, two windows, at 393 (and the 1440 control).

## Worker-brief scars

- **Touch is the proof:** a narrow screenshot alone is not a phone walk; a mouse click does not count at 393.
- **Errors never overlap UI:** a chip or bar that runs under a verb is a defect even when the verb still owns its hit point (G5).

## Effort (not a promise)

Grounding size: not sized as one move. PROVISIONAL.

## Notes

- 2026-10-03 — **Muad'Dib's ruling (aftercare, decision 5 narrowed):** when the front desk window already hosts the aftercare slot for the arriving card (`web/src/components/AmbientLayer.tsx` `findAftercareSlot`, its front-window branch `frontWindowAftercareSlot`), the card lands there, Capture does not open, and the front window stays. In every other case decision 5 stands: Capture opens and the front window iconifies. Found by the build: the ratified rule iconified the meeting's own record in Meetings when its own card arrived (`tests/e2e/test_hs202_first_use_smoke.py` `record-refresh` red at 393). Built in `web/src/desk/chair/ChairDesk.tsx`; fenced by `aftercarePhone.philo1317.test.tsx` (both branches) and the glass leg S6 (`C7-6e`, `C7-6f`).
- 2026-10-02 — canvas drawn for the owner's ruling, NOT RATIFIED: `assets/story-17-canvas/` (README lists the boards, the acceptance line each answers, the forks and the limits; it includes the owner's ruling that an arriving aftercare card opens Capture at 393). Drawn by a Fedaykin on main `76c361537`; unchecked, awaiting Astra's check, then the owner.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
