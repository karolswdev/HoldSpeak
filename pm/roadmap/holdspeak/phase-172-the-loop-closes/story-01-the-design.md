# HS-172-01 — The design

- **Project:** holdspeak
- **Phase:** 172
- **Status:** in-progress
- **Depends on:** Phase 170 merged
- **Unblocks:** HS-172-02, HS-172-03, HS-172-04, HS-172-05, HS-172-06, HS-172-07
- **Owner:** unassigned

## Problem

Every face in 172 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Loop Closes introduces new face regions (the PROPOSAL card in NEEDS
YOU, the People card with Watch-derived data, the suggested source row,
People in the Room and the shade) and modifies existing ones (the 1:1
brief). Without artboards these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The PROPOSAL card in NEEDS YOU (Confirm / Edit / Drop; the
    decision's provenance line: meeting, segment, speaker, timestamp).
  - The People card in the Room and in the shade (PRs waiting, review
    latency, commitments overdue, last meeting summary).
  - The suggested source row in the Room (offered, not applied; the
    repo/issue mention provenance).
  - People as a reachable section from the Room at 393.
  - The auto-intel status token on the Room's meeting section (running,
    done, the count of extracted items).
  - The 1:1 brief with Watch-derived data (the enrichment).
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [ ] Artboards at 1440 + 393 on the ratified shell for every new face
      region (Article IX.2; UX-CANON.md rule E.1).
- [ ] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [ ] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [ ] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [ ] The PROPOSAL card shows provenance (meeting, speaker, timestamp)
      without egressing content (Article III).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The PROPOSAL card face: does it live in the Room's NEEDS YOU section
  as a LedgerRow, or does it deserve its own well? The existing
  follow-through Card shape (follow_through_service.py:66) has the
  provenance fields; the face should show them.
