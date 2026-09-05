# HS-173-01 — The design

- **Project:** holdspeak
- **Phase:** 173
- **Status:** in-progress
- **Depends on:** Phase 172
- **Unblocks:** HS-173-02, HS-173-03, HS-173-04, HS-173-05
- **Owner:** unassigned

## Problem

Every face in 173 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Steward's Hand and Voice introduces new face regions (the model-
drafted update card with the egress chip, the reviewer-latency and
issue-aging NEEDS YOU rows, the nudge approval card with its receipt,
the release-readiness scorecard, the flaky-CI and merge-queue tokens)
and modifies the existing update draft view. Without artboards these
cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The model-drafted update card (prose body, claims sidebar with
    refs, unverified markers, the egress chip on the card).
  - The reviewer-latency NEEDS YOU row (person name, median hours,
    PR count, the nudge verb).
  - The issue-aging NEEDS YOU row (issue key, time-in-status, assignee).
  - The nudge approval card (the proposed comment, the target PR, the
    Approve / Skip verbs, the receipt with the comment URL).
  - The release-readiness scorecard row (per-signal indicators:
    green/amber/red).
  - Flaky-CI and merge-queue tokens in the Room.
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
- [ ] The nudge approval card shows the proposed comment text, the
      target PR, and the receipt placeholder.
- [ ] The egress chip appears on the model-drafted update card
      (Article III).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The nudge approval card is a constitutional moment: the face must
  make the external write unmistakable (Article V). Counsel reviews
  the card's design for clarity before the owner.
