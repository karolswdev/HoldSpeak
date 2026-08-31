# Phase 159 - Project Rooms: The Interview (P1a)

**Last updated:** 2026-08-31 — 4/7 DONE: the wire is live (20 routes, the full happy walk through the real app, 409 law for dead sessions, api-surface 594). NOW: 05 the face ∥ 06 the walk — then the beauty pass and THE OWNER'S SHOTS.

## Goal

Creating a Project becomes an interview that installs an operating
contract — not a CRUD form. A durable setup session asks two
questions, recommends concrete NATIVE Watches from what the desk
already knows (Meetings, Decisions, Door, evidence), compiles an
inspectable brief, and finalizes ATOMICALLY into a Project plus
selected tested Watches — while `connector_watches` graduates to
`WatchSpec@1` and every legacy Watch keeps running untouched.
Domain slice P1a (SRS_DOMAIN_DRIVER §14) + setup slice V0-A
(SRS_PROJECT_INTERVIEW_WATCHES §15); INT-001..012, ACT-001..009,
§9 persistence, WAT-001/003 foundations. External providers (GitHub
P2a, Jira P7) are OUT — the native family (§8.3) is the flagship
here.

Constitution: Art VI (no false baselines — ACT-005), Art VII (no
modals; the interview lives in-world), Art IX (shots at 1440+393;
THE OWNER'S VERDICT closes the face). Art XI: native suggestion
reads are computation; model invocations do not enter P1a (INT-010's
deterministic path is the P1a implementation).

## Scope

- **In:** the seven stories below; PR from `feat/project-rooms-p1a-the-interview`.
- **Out:** external provider adapters/discovery (P2a GitHub, P7
  Jira), model-assisted suggestion ranking (deterministic only —
  INT-010), Watch scheduling/evaluate_due (P5), provider effects
  (V0-E), the Delta review flow (P2).

## Exit criteria (evidence required)

- [ ] §14 P1a exit: setup RESUMES after reload and opens a NON-EMPTY Project Room without external provider dependency (proven by the walk, story 06).
- [ ] `connector_watches` graduated additively to WatchSpec@1 (§9.3 columns; existing IDs/query_json/snapshot_json preserved; legacy Watches migrate as legacy non-Project specs and their refresh keeps working — proven on a real-DB copy + legacy compat tests).
- [ ] Finalization is ONE atomic transaction (ACT-004): Project + selected Watches + bindings + baseline — or a recoverable draft; baselines emit NO false historical events (ACT-005).
- [ ] Abandoning setup never leaves a hollow active Project (INT-006).
- [ ] Shots at 1440+393 on a rig-booted hub; beauty pass; THE OWNER'S SHOT VERDICT closes story 05 and holds the merge word.
- [ ] Sweep zero true branch-new; web gates green; counsel close zero open must-fix.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-159-01 | The watch graduation (WatchSpec@1 columns + §9 tables, legacy intact) | done | [story-01-the-watch-graduation](./story-01-the-watch-graduation.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-159-02 | The watch service (one façade; ReactionService compat) | done | [story-02-the-watch-service](./story-02-the-watch-service.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-159-03 | The setup service (durable session, native suggestions, atomic finalize) | done | [story-03-the-setup-service](./story-03-the-setup-service.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-159-04 | The setup routes (HTTP §10, command contract, api-surface) | done | [story-04-the-setup-routes](./story-04-the-setup-routes.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-159-05 | The interview face (two questions, live brief, activation — shots + verdict) | backlog | [story-05-the-interview-face](./story-05-the-interview-face.md) | - |
| HS-159-06 | The walk (reload-resume → finalize → populated Now, on glass) | backlog | [story-06-the-walk](./story-06-the-walk.md) | - |
| HS-159-07 | The close (gates, suite amendments, final summary) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

CHARTERED. Chain: 01 → 02 → 03 → 04 → 05/06 → 07; the 05 face's
scaffolding may start against 04's frozen route contract. Laws
carried forward: workers scoped tests only; isolated HOME via
scratch scripts; build the web bundle before EVERY shot run;
fixtures speak the backend's dialect; restore suite-churned PNGs
before staging; commit messages via `-F` files; absolute paths in
parallel shells.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Legacy Watch refresh breaks under graduation | medium | additive columns only; compat tests pin refresh_due/preview/diff before migration; migration is a backfill, not a rewrite | a red legacy reaction test |
| The interview becomes chat theater | medium | deterministic suggestions from real desk facts; the compiled brief is always visible (INT-011); no model in P1a | a suggestion not traceable to a desk fact |
| Finalize leaks partial state | medium | one transaction; abandon/expire tests; INT-006 fence | a hollow active Project in any test |
| A second Watch lifecycle sneaks in | medium | WatchService is the ONLY new authority; ReactionService delegates or wraps (§2 ruling) | a write path to connector_watches outside the façade |
