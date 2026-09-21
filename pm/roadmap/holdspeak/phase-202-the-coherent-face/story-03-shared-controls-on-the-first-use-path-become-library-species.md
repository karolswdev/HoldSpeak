# HS-202-03 - Shared controls on the first-use path become library species

- **Project:** holdspeak
- **Phase:** 202
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

From the surface inventory of 2026-09-20 (`docs/internal/SURFACE-INVENTORY-2026-09-20.md`, §6 story 03; appendices 01–04; Astra's check `docs/internal/checks/surface-inventory-astra.md`). The Seven Tenets govern: first-use first (2), one obvious move (3), the component framework (5), Workbench 2.0+ (6); Articles III and VI; UX-CANON A.

## Scope

- **In:** Menu items, wing tabs, the dock, DeskEditor's controls, and the consumers those flows touch (bounded by the 157-site source census, migrated in this order; the rest ledgered)
- **Out:** everything the inventory's §6 ledger records; faces the five owner jobs do not touch; the broad census numbers as gates (they are diagnostics re-run at phase close).

## Acceptance criteria

- [ ] the source-button ratchet moves down by the migrated sites; no raw control on the five jobs' screens
- [ ] Every change has a fence proven red first on a real isolated hub; shots at 1440 and 393 in this story's assets; the first-use smoke (story 01) green after the change.
- [ ] Every verb the library Button; no prose; no modal; no counter of zero; one filled primary per window; labels in ASD-STE100.

## Test plan

- **Unit:** the fences the story names; vitest for face rules.
- **Integration:** the first-use smoke at both widths; the focused rigs the story touches.
- **Manual / device:** shots; story 06 is the owner's sitting.

## Notes / open questions

Lanes are assigned at build time under TWO-BRAINS §4 (default: Astra takes the backend and verification-harness work, Muad'Dib the faces; either brain checks the other's built lane before merge).
