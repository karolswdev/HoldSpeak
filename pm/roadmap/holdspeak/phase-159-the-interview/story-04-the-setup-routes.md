# HS-159-04 - The setup routes: the contract on the wire

- **Project:** holdspeak
- **Phase:** 159
- **Status:** backlog
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

## Notes / open questions

- Keep route handlers parse-and-serialize thin — the services own everything (the ProjectService docstring's own law).
