# HS-173-07 — The docs

- **Project:** holdspeak
- **Phase:** 173
- **Status:** in-progress
- **Depends on:** HS-173-06
- **Unblocks:** HS-173-08
- **Owner:** unassigned

## Problem

Every new face and behavior introduced in Phase 173 (the model drafter,
health signals, the reviewer nudge, the release-readiness scorecard)
must appear in the project's documentation. The reviewer nudge is the
first external write and requires explicit treatment in SECURITY.md.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the model-drafted update, the
    reviewer-latency NEEDS YOU row, the nudge approval card, the
    release-readiness scorecard.
  - docs/ARCHITECTURE.md: the steward's hand (policy gate -> effect ->
    receipt) as a Mermaid sequence diagram; the health signal
    derivation pipeline.
  - docs/SECURITY.md: the reviewer nudge egress statement (opt-in per
    project, behind the policy gate, receipted, via `gh pr comment`;
    Article III, Article V, Article XI).
  - README.md: update the feature list to mention the steward's
    bounded external effects (if not already covered).
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the 173 sections.

## Acceptance criteria

- [ ] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [ ] ARCHITECTURE.md contains the steward's hand diagram; the
      Mermaid renders (verified by the mmdc guard).
- [ ] SECURITY.md states the nudge is opt-in, receipted, and the only
      external write (Article III, Article V, Article XI).
- [ ] Every claim in the docs is truth-audited against the shipped
      tree (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- The SECURITY.md update for the nudge is constitutionally significant:
  it documents the first external write. Counsel reviews before the
  owner.
