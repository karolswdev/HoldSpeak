# HS-178-01 — The design

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** Phase 177 merged
- **Unblocks:** HS-178-02, HS-178-03, HS-178-04, HS-178-05, HS-178-06, HS-178-07
- **Owner:** unassigned

## Problem

Every face in 178 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Portfolio introduces a new Desk surface (the Projects window or
shade section) with Room rows, a depth pane, dependency alert rows, a
release-readiness aggregate, a portfolio section in the Monday brief,
and a PORTFOLIO verb in the command deck. Without artboards these
cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The Projects surface (Room rows with needs-you count, first WHY,
    release-readiness indicator, oldest-unresolved age; the urgency
    sort; the empty state).
  - The depth pane (cross-project needs-you rows grouped by project,
    severity and age ranking, filtering controls).
  - The dependency alert row (the two Rooms, the shared entity, the
    blocking state, the verb to open either Room).
  - The release-readiness aggregate (portfolio-level scorecard with
    per-signal roll-up across Rooms).
  - The Monday brief PORTFOLIO section (per-project summary, delta,
    scorecard indicator).
  - The command deck PORTFOLIO verb and per-Room verbs.
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
- [ ] The dependency alert artboard makes the cross-Room relationship
      unmistakable (the two project names and the blocking entity).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The decision between a full Desk window and a deeper shade section is
  the design story's first question. The owner's project count (3 as of
  the census) may not justify a full window; the shade's PROJECTS
  section from 171 may be the natural home for the deeper view.
