# HS-177-07 — The docs

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-06
- **Unblocks:** HS-177-08
- **Owner:** unassigned

**CONDITIONAL: this story proceeds only if HS-177-01 produces a GO
verdict. If the measured decision is CUT, this story is cancelled.**

## Problem

Every new face and behavior introduced in Phase 177 (Room grounding
for the Thread, the grounded ask with Watch entity citations, Chase
and Plan over Room data) must appear in the project's documentation.

## Scope

- In:
  - docs/USER_GUIDE.md: re-shot for the Chase thread with Room data,
    the grounded ask with Watch entity citations, the Plan thread with
    steward output.
  - docs/ARCHITECTURE.md: Room grounding in the Thread as a Mermaid
    diagram (thread turn -> hydrate_refs_detailed -> project_service /
    watch_sources -> grounding context -> model).
  - docs/SECURITY.md: statement that Room grounding reads from the
    local DB only (Article III); no live fetch to external sources
    during a thread turn.
  - README.md: one-line mention of the Thread at Work under the
    feature list if one exists.
- Out:
  - New standalone docs.
  - Rewriting existing docs beyond the 177 sections.

## Acceptance criteria

- [ ] USER_GUIDE.md re-shot for every new face (Article IX.2).
- [ ] ARCHITECTURE.md contains the Room grounding diagram; the
      Mermaid renders (verified by the mmdc guard).
- [ ] SECURITY.md states Room grounding stays local (Article III).
- [ ] Every claim in the docs is truth-audited against the shipped
      tree (Article VI.2).

## Test plan

- Unit: the mmdc guard passes (the existing Mermaid render check).
- Integration: n/a.
- Manual: read each doc section; verify the screenshots match the
  shipped face.

## Notes / open questions

- None.
