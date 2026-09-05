# HS-171-01 — The design

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** Phase 170 merged
- **Unblocks:** HS-171-02, HS-171-03, HS-171-04, HS-171-05, HS-171-06, HS-171-07
- **Owner:** unassigned

## Problem

Every face in 171 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Heartbeat introduces three new face regions (the shade PROJECTS
section, the macOS notification, the cadence row in Settings) and
modifies two existing ones (the dock badge, the command deck). Without
artboards these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The SystemShade PROJECTS section (Room rows with count and first
    WHY; the empty state; the aggregate headline).
  - The macOS notification (the count, the click target, the quiet
    state; the content-opt-in variant).
  - The cadence row in Settings (one row: the interval picker, the
    status chip, the next-check-at token).
  - The dock badge with the aggregate needs-you count.
  - The command deck PROJECTS section (Room entries with names).
  - The Monday brief entry in the shade (the recurring brief row).
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [x] Artboards at 1440 + 393 on the ratified shell for every new face
      region (Article IX.2; UX-CANON.md rule E.1).
- [x] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [x] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [x] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [x] The notification artboard names no Room content beyond the count
      (Article III.1) in the default variant.

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The artboard for Settings cadence row: does the owner want this under
  a "Rhythm" tile or a "Heartbeat" tile? Propose "Rhythm" (the existing
  cadence wiring uses that name internally); the owner decides.

## Ledger (2026-09-05)

Twelve boards (assets/mockups + story-01-shots); counsel RATIFY-W-C twice (the canvas, then the built tree) — every condition paid; canvas https://claude.ai/code/artifact/82c55045-4a19-4990-a8b5-569b91eb8647. Open: his word (after 170's).
