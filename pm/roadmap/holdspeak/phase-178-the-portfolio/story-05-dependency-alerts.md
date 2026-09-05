# HS-178-05 — Dependency alerts

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-02
- **Unblocks:** HS-178-08
- **Owner:** unassigned

## Problem

A PR in one repo can block a milestone in another, but today each Room
is isolated: no cross-Room entity comparison exists. When two Rooms
watch the same resource (or reference the same entity), and that entity
is in a blocking state, the owner should see a dependency alert.

## Scope

- In:
  - Dependency detection: at portfolio aggregate time, compare Watch
    entities across active Rooms. When an entity (identified by its
    canonical ref: repo + number for PRs, issue key for Jira) appears
    in two or more Rooms and is in a blocking state (review requested
    > 48h, CI failing, overdue commitment), emit a dependency alert.
  - The alert row in the Projects surface: the two (or more) project
    names, the shared entity, the blocking state, a verb to open
    either Room.
  - The alert is a read (no external write; Article V:5).
- Out:
  - Cross-source dependency detection (GitHub PR blocking a Jira
    issue) -- deferred to the design decision.
  - Automatic resolution of dependencies.
  - Dependency alerts for non-blocking shared entities (shared
    references alone do not trigger alerts).

## Acceptance criteria

- [ ] A dependency alert surfaces when a Watch entity referenced by
      two or more Rooms is in a blocking state (Article VI — honest;
      no alert for non-blocking shared refs).
- [ ] The alert row shows both project names, the shared entity, and
      the blocking state.
- [ ] A verb on the alert row opens either Room.
- [ ] Verified by a unit test with two seeded Rooms sharing one PR
      entity in a blocking state.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k dependency_alerts`
  - Two Rooms, one shared PR entity in blocking state: alert emitted.
  - Two Rooms, one shared PR entity NOT blocking: no alert.
  - Three Rooms sharing one entity: one alert naming all three.
- Integration: the alert renders in the Projects surface.
- Manual: the owner's desk (if two of his projects share an entity).

## Notes / open questions

- At the owner's current scale (3 projects), dependency alerts may be
  rare. The story is justified by the architecture: a portfolio that
  cannot see cross-Room dependencies is not honest about the desk's
  state.
- Cross-source detection (GitHub + Jira) depends on whether 173 or 174
  ships a cross-source entity resolver. If it does not exist, this
  story detects dependencies within a single source type only.
