# HS-170-01 - The census (every surface shot at 1440 + 393 on an isolated desk; the canon-violation scan across the web tree; one ranked table per face by Tuesday use × canon debt)

- **Project:** holdspeak
- **Phase:** 170
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-170-02
- **Owner:** unassigned

## Problem

The owner: "Fedaykin need to make a huge UX pass of everything. Is our canon kept?" Before a pass, the truth: what every face looks like today and where it breaks the canon.

## Scope

- **In:** a shot rig over every surface key in web/src/desk/applications.ts (both widths, the window shot, settle before every shot) → assets/census/<key>-<w>.png; a mechanical scan (raw buttons, sentences in JSX text, zero counters, prose helpers, non-library controls, missing egress chips near fetch sites, single-type-step faces, accent rails) → assets/census/violations.md with file:line; the ranked table assets/census/ranking.md (Tuesday use from the desk census × violations); docs/internal/UX-CANON.md ratified as the face canon.
- **Out:** any fix.

## Acceptance criteria

- [ ] Every surface key has a shot at both widths.
- [ ] violations.md lists every hit with file:line and the canon rule it breaks.
- [ ] ranking.md orders the faces; the orchestrator read every PNG.

## Test plan

tests/e2e/test_hs170_census_glass.py (isolated HOME, alone); the scan script under scripts/ux_canon_scan.py run on the tree.

## Delivered (2026-09-05)

- docs/internal/UX-CANON.md — the face canon (13 rulings in the owner's
  words; the species; the type steps; the grammar the scars taught; the
  review protocol), linked from CLAUDE.md's source canon.
- tests/e2e/test_hs170_census_glass.py — every surface key in
  applications.ts (17) shot at 1440 + 393 on an isolated seeded desk:
  36 PNGs + census.md (window · raw buttons · sentences · type steps ·
  clipped · zero counters · a human note per face).
- scripts/ux_canon_scan.py (+ smoke test) — 12 canon classes with
  file:line → violations.md / .json (671 hits: 147 raw buttons, 140 raw
  ids, 118 zero counters, 112 emoji glyphs, 51 raw controls, 43 prose,
  35 missing mics, 12 sentences, 8 accent rails, 4 one-step faces, 1
  missing egress) and ranking.md (Tuesday use × debt: PeopleCore,
  AttentionDrawer, ModelLibraryCore, ThoughtWorkspaceWindow,
  ProjectRoomCore, …).
- assets/census/orchestrator-read.md — the orchestrator's read of every
  shot: the desk ARRIVAL (a graveyard of empty wells and zeros), SPEAK
  (an engineer's console with a banned rail), the SETTINGS hub (emoji
  tiles), MEETINGS (`1 RECORDS`, `0 SEG`) proposed for the canvas in 04;
  Processes (eight zeros), People (one type step), Agents, Commands, the
  calendar snapshot and first-run setup lifted by the sweep.
- Evidence: the worker's run of the census rig was green (`1 passed in 96.97s`, 36 PNGs on disk); the orchestrator's CAPTURE of it (evidence-story-01.md, 2026-09-05) FAILED at the build-first step because three sweep lanes were mid-edit on web/src — the scan's smoke test passed in the same capture. RE-CAPTURED green at bd47897e (2026-09-05T05:18Z, exit 0) after lanes P/T/D landed — the 36 PNGs under assets/census are now the AFTER-sweep census; the before-sweep shots live in git at a80c1967..6987d94e.
