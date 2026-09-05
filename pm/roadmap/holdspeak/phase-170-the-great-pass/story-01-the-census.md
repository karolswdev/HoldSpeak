# HS-170-01 - The census (every surface shot at 1440 + 393 on an isolated desk; the canon-violation scan across the web tree; one ranked table per face by Tuesday use × canon debt)

- **Project:** holdspeak
- **Phase:** 170
- **Status:** in-progress
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

## Delivered

_(pending)_
