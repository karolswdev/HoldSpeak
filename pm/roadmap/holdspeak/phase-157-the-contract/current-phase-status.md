# Phase 157 - Project Rooms: The Contract (P0)

**Last updated:** 2026-08-31 — HS-157-01 DONE (the ref grammar RULED: `people:` canonical, `person:` alias — evidence reversed the charter's guess); 03/04 in flight; building. Owner rulings recorded: POSITIONING "Watches (Project-scoped)" row RATIFIED; EverDriven delivery rides GitHub (P2a proves; Jira P7 follows with a real adapter).

## Goal

Freeze the contracts today's Project subsystem holds implicitly —
qualified refs, command results, typed errors — and pin existing
Project behavior (service, routes, Web surface, MCP registration)
under characterization tests, so the Project Rooms graduation can
proceed without ever breaking the promise AD-PRJ-004 makes: every
citizen keeps its own truth. Small, unglamorous, non-negotiable.

First phase of the Project Rooms arc. Charter grounded in the vetted
SRS suite (`docs/internal/project-rooms/`, PR #519): domain slice P0
(`SRS_DOMAIN_DRIVER.md` §14), REF-001..004, API-001..003, TST-008.
Constitution: Art VI (honest by construction), Art IX (proof over
claim); the arc ahead answers to Art XI (the kernel) via NFR-009.

## Scope

- **In:** the five stories below; PR from `feat/project-rooms-p0-the-contract`.
- **Out:** any schema change, any new endpoint, any Web feature work,
  the `project.*` MCP family, Watch graduation — those are P1+ phases.
  Characterization changes NO behavior.

## Exit criteria (evidence required)

- [ ] Current Project behavior is protected: characterization tests cover ProjectService (CRUD/archive/meeting/resource/summary/since-last-meeting), all 18 `/api/projects*` routes, the Web Project Memory registration/opening seam, and the MCP family registration truth — all green under isolated HOME.
- [ ] Schema/API names are agreed: the P0 contract doc records the frozen result envelope (`result_kind`, `project_id`, `project_revision`, `changed_refs`, typed errors), the qualified-ref grammar, and the ID prefixes from SRS_DOMAIN_DRIVER §4 — and every name traces to the SRS suite (a discovery that invalidates one updates the suite before or with the code).
- [ ] The `person:`/`people:` ref-prefix drift is settled (REF-003): one canonical type, backward-compatible aliases, round-trip tests, and a fence that keeps new Project code off feature-local string splitting.
- [ ] Sweep name-diff clean vs main (zero branch-new); web baseline zero branch-new; counsel close with zero open must-fix.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-157-01 | The qualified ref (one grammar, aliases, the fence) | done | [story-01-the-qualified-ref](./story-01-the-qualified-ref.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-157-02 | The result contract (envelope, typed errors, ID prefixes) | backlog | [story-02-the-result-contract](./story-02-the-result-contract.md) | - |
| HS-157-03 | The service characterization (ProjectService + routes) | in-progress | [story-03-the-service-characterization](./story-03-the-service-characterization.md) | - |
| HS-157-04 | The surface characterization (Web + MCP registration) | in-progress | [story-04-the-surface-characterization](./story-04-the-surface-characterization.md) | - |
| HS-157-05 | The close (gates, suite updates, final summary) | backlog | [story-05-the-close](./story-05-the-close.md) | - |

## Where we are

CHARTERED 2026-08-31 against the vetted SRS suite on PR #519
(handover: `docs/internal/project-rooms/HANDOVER-IMPLEMENTATION.md`).
All 15 handover §1 ground-truth anchors re-verified against
origin/main at charter time (`56d7ca2c`) — every one holds; nothing
moved. The `person:`/`people:` drift confirmed live:
`holdspeak/services/thread_service.py:311` splits `person:` while
`holdspeak/services/people_service.py:784,799` emits `people:`.
No `project.*` MCP family exists (15 registered families; Watch tools
live in `reactions.py`). #519 merged `e7e56e1e` (2026-08-31); the
owner ratified the POSITIONING canon row and ruled delivery = GitHub
(`gh`), with Jira parity following GitHub proof on a real adapter.
HS-157-01 shipped `holdspeak/refs.py` + CONTRACTS-P0.md: REF-003
ruled `people:` canonical on runtime-safety evidence (6/6 emitters,
5/6 parsers), 58 tests + the REF-001 fence green under isolated HOME.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Characterization drifts into refactor | medium | pin behavior as-is; a P0 commit changes no runtime semantics | any behavior change in a characterization diff |
| Ref canonicalization breaks Desk consumers | medium | aliases accepted on parse; existing emitters untouched in P0 | web baseline branch-new; a changed emitted ref |
| Contract doc invents names the SRS never agreed | low | every name traces to the suite; discoveries amend the suite before/with code | a name in code absent from the SRS + no suite edit |
| Charter built on stale anchors | low | anchors re-verified at charter (see Where we are) | an anchor miss during implementation |
