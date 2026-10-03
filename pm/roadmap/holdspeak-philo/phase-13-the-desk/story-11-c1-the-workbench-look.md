# PHILO-13-11 - C1 The Workbench look (the canvases; the face gate)

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** the owner's ratification of this charter (the canvas starts in wave one, beside Wave A and B0); the build waits on the owner's ratification of the canvas
- **Unblocks:** PHILO-13-06, -08, -15, -17 (their canvases are drawn on this material); PHILO-13-12 to -18 and C3-W (no C face is built before its canvas is ratified); A1-F (its artboard is in this set)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C1 (PROPOSAL §3, Wave C); fork 1, "All the way"
- **Closure finding:** PROPOSAL §2 truth 6; `grounding/faces.md:26`; `grounding/checks/faces-astra.md` finding 7; `grounding/checks/proposal-astra.md` finding 4
- **Canvas:** the frame, the window chrome and the Chair, at 1440 and 393, on the real product with a harness shim; owner-ratified before build

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The frame, the window chrome and the Chair look and behave like Workbench 2.0+ on steroids ("All the way", fork 1). Canvas first; his ratification; then the build matches the canvas.

## Problem

The Chair at 1440 reads as a black web dashboard of rows and chips, not a Workbench desk of windows, gadgets and icons (`grounding/shots/surfaces/01-chair-pop-1440.png`, `01-chair-pop-393.png`; `grounding/faces.md:26`). The Room already reads as a windowed desk (`grounding/shots/surfaces/64-room-pop-1440.png`), so the gap is the frame and the Chair, not every body (`grounding/checks/proposal-astra.md` finding 4). Nineteen host files call `DeskWindowFrame`; its chrome uses the library Button and WorkMenu (`web/src/desk/components/DeskWindow.tsx:823`, `:861`; `grounding/structure.md:151`). There is no depth gadget, no zoom between two remembered sizes, no screen title bar, no live AppIcon (`grounding/faces-jobs.md:146-148`). The Dock overflows 1440 (1510 px wide, −35 to 1475; `grounding/faces-surfaces.md:75`).

## Scope

- **In:**
  - **The canvas** (UX-CANON A.2): the frame (menu bar as a screen title bar, Dock), the window chrome (one gadget set), the material tokens, the Chair composed of windows, and the named artboard **"Parked and Restore"** (A1-F: the Parked filter, Restore and the `PARKED` receipt on Meetings and the Workbench window), at 1440 and 393. Astra checks; the owner ratifies; his word recorded verbatim.
  - **The build** after ratification: the material as tokens worn by every `DeskWindowFrame` host; the gadget set in the chrome (`DeskWindow.tsx`, `window/*`); the screen title bar; the Chair as windows (`web/src/desk/chair/**`); all CSS.
  - The Dock stays inside the viewport at 1440 with long window titles.
- **Out:** redesigning every body (bodies inherit the material through `DeskWindowFrame`; PROPOSAL C1); the gadgets' behaviour (C2); live AppIcon data (C3); the phone layout (C7); the type floor sweep (C8); the Floor.

## Acceptance criteria

The canvas criteria, each checkable on the shot (PROPOSAL C1):

- [ ] (1) Every window carries one gadget set — close, depth, zoom — in one place.
- [ ] (2) A screen title bar names the front window and the time.
- [ ] (3) One material (surface, bevel, focus) is defined as tokens and worn by every `DeskWindowFrame` host.
- [ ] (4) The Chair is composed of windows (brief, needs you, the week), not one scrolling page.
- [ ] (5) The 12 px floor and library Buttons throughout.
- [ ] (6) Both widths (1440 and 393).
- [ ] (7) Live state is drawn on the AppIcons, not in a status window.

And:

- [x] Astra's check of the canvas recorded; the owner's ratification recorded verbatim before the first C1 face commit. (r1–r5, r5 RATIFY; owner 2026-10-02, see "RATIFIED" below)
- [ ] The build matches the ratified canvas, board beside shot, at both widths (touch at 393).
- [ ] The Dock fits 1440 with a long window title (red on main, `grounding/shots/surfaces/64-room-pop-1440.png`).
- [ ] Every verb the library Button; no modal; no prose; no counter of zero; the web baseline has zero branch-new failures.
- [x] The "Parked and Restore" artboard is drawn at both widths and ratified with the rest of the set (or on its own, if A1-F is ready first).
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of its canvas (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` holds this lane's NEW cases (`--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`. An existing case runs from the atlas that holds it (named below).
- **Canvas:** the harness boards through the real hub on an isolated HOME at both widths; shots under `assets/story-11-canvas/` (the Phase 10–12 pattern, `../phase-12-send-from-the-floor/assets/story-02-canvas/`).
- **Focused:** a token fence (every `DeskWindowFrame` host wears the material tokens); web unit on the chrome; `uv run python scripts/check_web_baseline.py --run`.
- **Atlas:** the Chair arrival case `case.j10.arrival_generate_brief.populated` (in `docs/internal/philo/graph/atlas.json`) and the window-chrome case `case.p13.close.intelligence_gone` (in `atlas-phase13-muaddib.json`), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** the Chair, a body window, the frame, at 1440 and 393 (touch).

## Worker-brief scars

- **Build what was ratified** (UX-CANON A.2): the board beside the shot every round.
- **Lead/primary splits are species bugs** (A.1): fix the species in `surface.css`, never a face override.
- **Fences that name old words:** chrome or Chair fences that assert old structure change with it, in the same commit; none is deleted to make the build green.

## Effort (not a promise)

Grounding size: not sized (new in PROPOSAL r2). PROVISIONAL; the long pole of the faces lane.

## Notes

- 2026-10-03 — **The window title bar: B, Workbench refined (owner pick).** The owner said the C1 title bar "looks terrible"; on the page https://claude.ai/artifact/KF7PkJvexbmfuUkdPPHu3E (the control + three directions, `assets/titlebar-canvas/`) he answered, verbatim: **"B"**. B replaces the solid title plate: fine stripes on the front bar only, inactive bars flat, the title on the bar's own blue cut-out, one gadget grid; 393 keeps 44 px. Build: `assets/titlebar-build/`.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

## RATIFIED by the owner — 2026-10-02

On the ratification page (https://claude.ai/artifact/Sdx4gWvAPcXPhWF6Cz6tVZ, the 20 boards of round 3e at `assets/story-11-canvas/`), the owner answered, verbatim:
- The look: **"Ratify, build it"**
- Direction: **"Steel (Recommended)"**
- Park: **"One press (Recommended)"** — no confirm; Restore undoes it
- Capture: **"Yes (Recommended)"** — a fourth Chair window on desktop; on demand from the Speak AppIcon on the phone

Astra's canvas checks r1–r4 DO-NOT-RATIFY, all paid; **r5 RATIFY** (`checks/canvas-astra-r1..r5.md`). Both brains agree; no open dissent. The settled design for build is `design/workbench-look.md`; every C-story face (and A1-F, B1, B3, C5, C7) cites this ratification in its merge record (the gate).
