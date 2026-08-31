# HS-159-03 - The setup service: two questions, real suggestions, one atomic finalize

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
- **Depends on:** HS-159-02
- **Unblocks:** HS-159-04
- **Owner:** unassigned

## Problem

AD-PRJ-009: creation is an interview that compiles a durable
structured contract. INT-001..012 govern the session; §8.3 names the
provider-free native family that MUST ship with the flow; ACT-004/005
make finalization atomic and baselines honest; INT-006 forbids hollow
Projects.

## Scope

- **In:** `ProjectSetupService`: `start/get/answer/suggest/finalize/
  abandon` over the §9.1 tables. Sessions: state machine §5
  (`active(outcome→signals→…)→completed|abandoned|expired`),
  autosave-by-design (every accepted answer persists — INT-005),
  answers append-only with revisions, original text preserved
  separately from normalized values (INT-004). Suggestions:
  DETERMINISTIC (INT-010 is the implementation, not the fallback)
  over the native family §8.3 — associated/recent Meetings, linked
  Decisions + review-due, Door/follow-through overdue/stale,
  evidence silence, update/review due — each suggestion carrying
  source/subject/conditions/action/cadence/readiness/rationale
  traceable to a REAL desk fact (INT-007/008). Proposals persist in
  `watch_setup_proposals` with test_state; native test runs through
  WatchService.test. `finalize()` calls ONE
  `ProjectService.create_from_setup()` transaction (ACT-004):
  Project (§5.1 fields from the interview) + selected passed Watches
  activated + `project_sources` bindings + baselines (no historical
  events — ACT-005) + setup session completed — or everything rolls
  back to a recoverable draft. Blank path: explicit, active, no
  Watch required (INT-002). Abandon/expire leaves NO Project
  (INT-006). Cadence presets §4.1 stored on the spec's trigger.
- **Out:** external providers, model assistance, Web (05), routes (04).

## Acceptance criteria

- [ ] A session survives simulated reload at EVERY stage (state + answers + proposals rehydrate exactly — INT-005); abandon/expire leaves zero Projects/Watches (INT-006).
- [ ] Suggestions are deterministic and fact-traceable: fixture desks yield exact-match suggestion tables; a desk with nothing yields the honest Blank-forward path, never invented subjects (PROV-011 spirit).
- [ ] finalize() atomicity: fault injection at each step rolls back ALL of it; success activates only passed proposals (ACT-003: failed ones repaired/removed/disabled, never active).
- [ ] Baseline honesty: activation emits zero historical transition events (ledger asserted).
- [ ] Every mutation rides the revision-law envelope; the 158 characterization pins hold.

## Test plan

- **Unit:** `tests/unit/test_project_setup_service.py` (state machine, resume, suggestions truth tables, finalize atomicity, Blank, abandon).

## What shipped

- `ProjectSetupService`: start/get/answer/suggest/select/clarify/
  test_proposal/finalize/abandon over the §9.1 tables. Stage machine
  outcome→signals→proposals→review→completed|abandoned|expired;
  EVERY stage rehydrates (session + latest-revision answers + all
  proposals) — the resume seam. Answers append-only, original
  preserved beside normalized (INT-004).
- DETERMINISTIC native suggestions (§8.3) with a fixture truth
  table: meetings activity, decision review-due, overdue Door,
  stale follow-through — each proposal a full WatchSpec@1 draft
  (native provider, real-ID scopes, validated conditions,
  project.observe, cadence preset, a rationale naming the fact +
  count). An empty desk yields ZERO proposals and the Blank path —
  nothing invented.
- `ProjectService.create_from_setup`: ONE connection writes
  everything — project row, each selected+PASSED watch (active,
  baseline established, zero events), rules, project_sources
  bindings, change row, ledger event, command record. Fault
  injection at project-INSERT and watch-INSERT both roll back to a
  recoverable active session with zero Project/Watch rows (ACT-004/
  INT-006). Failed/untested proposals refused from activation
  (ACT-003). Blank finalize lawful (INT-002).
- test_proposal reads the REAL seams (meetings/decisions/
  FollowThroughService.board); `evidence` returns [] honestly — no
  native read path exists yet (noted for 04/06).
- 42 new tests; scoped set 227 passed (orchestrator re-ran via
  capture). No automations.py changes needed — create_from_setup
  writes through one conn directly.

## Notes / open questions

- `create_from_setup` lives on ProjectService (§10's ruling) — the setup service composes, never writes Project rows itself.
- FOUND: a ternary-precedence expiry bug (`a > b.replace(...) if c else b` parses as `(a > ...) if c else b` — a truthy datetime in the else branch); split into statements. Worth a lint thought someday.
- Decisions seeding gotcha: `source_state` CHECK allows only linked|source_deleted.
