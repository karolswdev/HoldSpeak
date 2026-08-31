# HS-157-03 - The service characterization: ProjectService + routes pinned

- **Project:** holdspeak
- **Phase:** 157
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-157-05
- **Owner:** unassigned

## Problem

P1 reconciles new columns onto `projects`, adds revisions, and
graduates the service. Nothing may break what exists: legacy
Projects stay readable/restorable (DOM-011), legacy endpoints stay
compatible (API-006), and TST-008 demands regression cover for
current CRUD, meeting association, resources, summary, and archive.
Today that cover is partial and scattered; pin it deliberately
before anything moves.

## Scope

- **In:** characterization tests over the REAL service + routes as
  they behave today (isolated HOME, real FastAPI app, real DB file —
  the 153/154 route-test pattern): all 21 public
  `ProjectService` methods (`list/create/get/update/archive`,
  `list_briefings`, `list_meetings`, `list_resources`,
  `add/remove_resource`, `list_resource_relationships`,
  `associate/disassociate_meeting`, `list_meeting_projects`,
  `since_last_meeting`, `summary`, `list_action_items`,
  `list_artifacts`) and all 18 `/api/projects*` +
  `/api/meetings/{id}/projects` + `/api/desk/relationships/*` routes
  (`holdspeak/web/routes/projects.py:32-209`). Response SHAPES pinned
  (keys, types, status codes, 404 paths), not just 200s. Archive →
  what DELETE actually does today, recorded as-is.
- **Out:** fixing any oddity found (file an issue/notes entry;
  characterization records truth, it does not improve it); schema
  changes; new endpoints.

## Acceptance criteria

- [ ] Every public ProjectService method has at least one characterization test asserting its current result shape and its principal/404 error behavior.
- [ ] Every route in projects.py has a characterization test through the real app: success shape + at least one failure path each.
- [ ] Tests run green under isolated HOME (scratch-script law) and are deterministic; no reliance on the owner's real DB.
- [ ] Any surprising current behavior is recorded in the story's Notes (and, if it contradicts the SRS baseline claims, the suite is amended before or with the code).

## Test plan

- **Unit/integration:** `tests/unit/test_project_service_characterization.py`, `tests/integration/test_project_routes_characterization.py` (names may follow repo convention).
- **Regression:** full-suite name-diff vs main at the close.

## What shipped

- `tests/unit/test_project_service_characterization.py` — 62 tests:
  all 18 public ProjectService methods pinned (result shape: keys,
  types, defaults; not-found/validation behavior each).
- `tests/integration/test_project_routes_characterization.py` — 46
  tests: all 18 routes through the real FastAPI app (success shape +
  at least one failure path each).
- No runtime code touched; no pre-existing test modified. Verified
  with the pre-existing `test_web_project_kb_api.py` in the same run:
  `140 passed in 36.19s` under isolated HOME (orchestrator re-ran).

## Notes / open questions

Characterization surprises RECORDED, deliberately not fixed (P0 law):

1. **DELETE is archive** — `DELETE /api/projects/{id}` (projects.py:79)
   calls `archive_project`; the project stays retrievable. Semantically
   misleading verb; P1's command contract should name it honestly.
2. **Three flavors of 404 wording** — "Project not found" vs "Unknown
   project: <id>" vs "Unknown Project: <id>" (projects.py:27,37,104).
   The HS-157-02 error-code table is the cure; route migration is P1.
3. **`success`-key asymmetry in 404s** — GET 404s lack `success`;
   PATCH/DELETE 404s carry `success: false`.
4. **Invalid relationship ValueError passes raw through the service**
   (project_service.py:97-101 → relationships.py:190; the route
   catches it at projects.py:114). The service boundary should own
   typed validation — P1's `expected_revision`/command work fixes it.

None contradict the SRS baseline claims; no suite amendment needed.
