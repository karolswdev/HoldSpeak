# HS-172-09 — The docs

- **Project:** holdspeak
- **Phase:** 172
- **Status:** done
- **Depends on:** HS-172-08
- **Unblocks:** HS-172-10
- **Owner:** unassigned

## Problem

Every new face and behavior introduced in Phase 172 (the auto-intel
trigger, PROPOSALS in NEEDS YOU, the People resolver, the enriched 1:1
brief, suggested sources, People in the Room) must appear in the
project's documentation.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the PROPOSAL card in NEEDS YOU,
    the People card, the suggested source row, auto-intel status in
    the Room.
  - docs/ARCHITECTURE.md: the loop-closes pipeline (meeting capture ->
    intel -> extraction -> proposals -> confirm -> decision record +
    commitment) as a Mermaid sequence diagram.
  - docs/SECURITY.md: the People resolver boundary statement (all
    matching in-memory inside the encrypted store; never egressed).
  - README.md: one-line mention of the loop under the feature list if
    one exists.
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the 172 sections.

## Acceptance criteria

- [x] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [x] ARCHITECTURE.md contains the loop-closes pipeline diagram; the
      Mermaid renders (verified by the mmdc guard).
- [x] SECURITY.md states the People resolver stays inside the
      encrypted boundary (Article III).
- [x] Every claim in the docs is truth-audited against the shipped
      tree (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
