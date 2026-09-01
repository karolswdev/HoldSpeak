# HS-159-04 - The setup routes: the contract on the wire

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
- **Depends on:** HS-159-03
- **Unblocks:** HS-159-05, HS-159-06
- **Owner:** unassigned

## Problem

§10 names the HTTP surface: `/api/project-setups/{session_id}/...`,
`/api/projects/{project_id}/watches`,
`/api/watches/{watch_id}/test|baseline|pause|retire`. Web (05) and
the walk (06) build against these; the command contract (command ID,
expected revision where applicable, structured result, typed error)
applies to every command.

## Scope

- **In:** routes for start/get/answer/suggest/finalize/abandon setup;
  list/get/update/test/baseline/pause/retire Watch; list Project
  watches. Registered per the front_door pattern (routes module +
  __init__ + web_server); owner-scoped like siblings; typed errors
  with the repo's conflict statuses; api-surface regenerated.
  Route-level tests through the real app (success + failure paths
  each).
- **Out:** provider/discovery routes (P2a), evaluations/effects
  routes (P5), MCP (P6).

## Acceptance criteria

- [ ] Every §10 path in scope exists with success + failure tests; unknown session/watch → 404; validation → 400; conflicts → the repo's conflict status.
- [ ] Finalize returns the envelope (result_kind, project_id, project_revision, changed_refs incl. the new project + watches).
- [ ] api-surface manifest regenerated; fence green; 158/157 characterization pins untouched.

## Test plan

- **Integration:** `tests/integration/test_project_setup_routes.py` via the real app.

## What shipped

- `holdspeak/web/routes/project_setup.py` (10 routes: start/get/
  answers/suggest/select/deselect/clarify/test/finalize/abandon) +
  `holdspeak/web/routes/watches.py` (10: list ×2/get/update/test/
  baseline/pause/resume/retire/rules) — parse-and-serialize thin,
  owner-scoped, registered per the front_door pattern.
- Status law: 404 unknown ids; 400 validation (incl. WatchCondition@1
  refusals through PUT rules); 409 for expired/abandoned/idempotency
  conflicts (the sibling ConflictError convention) — expired sessions
  transition ON READ and then refuse mutation with 409.
- Finalize returns the envelope (result_kind/project_id/
  project_revision/changed_refs).
- api-surface 574 → 594 (+20), fence green, both docs regenerated.
- 30 integration tests through the REAL app incl. the full happy walk
  (start → answers → suggest → select → test → finalize → the
  created Project visible via /room with its watch binding), Blank
  finalize, abandon-then-finalize refusal, watch round-trips.
  Scoped set 206 passed (captured).

## Notes / open questions

- Keep route handlers parse-and-serialize thin — the services own everything (the ProjectService docstring's own law).
- Test-harness gotcha: TestClient composes no auth middleware — the suite injects an OWNER-stamping middleware matching production; the face's fixtures should mirror the REAL wire shapes these routes emit (the 158 law).
