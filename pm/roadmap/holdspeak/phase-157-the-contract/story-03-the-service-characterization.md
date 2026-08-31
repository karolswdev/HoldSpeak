# HS-157-03 - The service characterization: ProjectService + routes pinned

- **Project:** holdspeak
- **Phase:** 157
- **Status:** in-progress
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

## Notes / open questions

- Existing `tests/integration/test_web_project_kb_api.py` covers part of this — extend rather than duplicate; the story's value is the COMPLETE pin, method by method, route by route.
