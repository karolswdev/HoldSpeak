# HS-123-05 — Projects and projections

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01
- **Unblocks:** HS-123-12
- **Owner:** unassigned

## The thesis (the bar)

Projects are the desk's durable organizing context. CRUD is only the start:
briefings, resources and their relationships, meeting association, summaries,
action items, artifacts, and since-last-meeting views must all use one
principal-aware domain boundary. Projections likewise represent durable
presentation state, not an HTTP-only toggle.

When this ships, `ProjectService` owns every project operation in the audited
module and `ProjectionService` owns projection listing/presentation updates.
Their routes are thin adapters with no direct persistence or authorization
logic.

## Phase 122 pattern to follow

Apply the HS-122 service extraction pattern and HS-123-01 errors:

- Compose each service once from the database and narrow domain collaborators;
  never inject `WebContext`, FastAPI request/response objects, or a router.
- Every public operation accepts an explicit `Principal` first. It returns a
  transport-neutral result or raises a shared service error code; the route
  maps that code to the established HTTP response.
- Preserve existing payloads, status codes, sorting, pagination/defaults, and
  relationship integrity. This is an ownership extraction, not a project data
  model change.
- The route may parse a path/query/body and serialize a service result. It may
  not look up a project, check membership, mutate a relationship, or write a
  projection itself.

## Required service contracts

Create `holdspeak/services/project_service.py` with public methods matching the
handler map below. At minimum: `list_projects`, `create_project`, `get_project`,
`update_project`, `archive_project`, `list_briefings`, `list_meetings`,
`list_resources`, `add_resource`, `remove_resource`, `list_resource_relationships`,
`associate_meeting`, `disassociate_meeting`, `list_meeting_projects`,
`since_last_meeting`, `summary`, `list_action_items`, and `list_artifacts`.

The service must centrally enforce project visibility and validate both sides
of a relationship/association before mutation. Retain current archive versus
hard-delete semantics, resource-reference canonicalization, relationship
ordering, meeting association idempotency/conflict behavior, and projection of
project-memory data.

Create `holdspeak/services/projection_service.py` with:

- `list(principal)`;
- `set_presentation(principal, projection_id, state)`.

`set_presentation` must validate the current presentation state payload and
persist exactly the durable state the route currently writes. It must not be a
client-only preference unless the existing endpoint is one.

## Audited handler map

### `holdspeak/web/routes/projects.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 26 | `api_list_project_briefings` — `GET /api/projects/{project_id}/briefings` | `ProjectService.list_briefings(principal, project_id)` | Medium — retain project access and briefing ordering. |
| 79 | `api_list_projects` — `GET /api/projects` | `ProjectService.list_projects(principal, filters)` | Medium — retain visibility, filters, ordering, and pagination/defaults. |
| 106 | `api_create_project` — `POST /api/projects` | `ProjectService.create_project(principal, payload)` | High — validate creation and preserve owner/provenance defaults. |
| 166 | `api_get_project` — `GET /api/projects/{project_id}` | `ProjectService.get_project(principal, project_id)` | Medium — preserve not-found versus forbidden behavior. |
| 190 | `api_update_project` — `PATCH /api/projects/{project_id}` | `ProjectService.update_project(principal, project_id, patch)` | High — retain patch validation and mutable-field restrictions. |
| 260 | `api_archive_project` — `DELETE /api/projects/{project_id}` | `ProjectService.archive_project(principal, project_id)` | High — archive semantics and response shape must not become hard delete. |
| 281 | `api_project_meetings` — `GET /api/projects/{project_id}/meetings` | `ProjectService.list_meetings(principal, project_id)` | Medium — retain association ordering/visibility. |
| 293 | `api_project_resources` — `GET /api/projects/{project_id}/resources` | `ProjectService.list_resources(principal, project_id)` | Medium — preserve canonical resource identity and access checks. |
| 305 | `api_add_project_resource` — `PUT /api/projects/{project_id}/resources/{resource_ref:path}` | `ProjectService.add_resource(principal, project_id, resource_ref)` | High — validate project/resource existence and idempotency. |
| 325 | `api_remove_project_resource` — `DELETE /api/projects/{project_id}/resources/{resource_ref:path}` | `ProjectService.remove_resource(principal, project_id, resource_ref)` | High — preserve absent-link/not-found behavior and integrity. |
| 336 | `api_resource_relationships` — `GET /api/desk/relationships/{resource_ref:path}` | `ProjectService.list_resource_relationships(principal, resource_ref)` | Medium — retain relationship traversal/filtering and redaction. |
| 363 | `api_associate_meeting` — `POST /api/projects/{project_id}/meetings/{meeting_id}` | `ProjectService.associate_meeting(principal, project_id, meeting_id)` | High — validate both records and retain duplicate/conflict behavior. |
| 379 | `api_disassociate_meeting` — `DELETE /api/projects/{project_id}/meetings/{meeting_id}` | `ProjectService.disassociate_meeting(principal, project_id, meeting_id)` | High — retain unlink and orphan-protection semantics. |
| 393 | `api_meeting_projects` — `GET /api/meetings/{meeting_id}/projects` | `ProjectService.list_meeting_projects(principal, meeting_id)` | Medium — preserve reverse association visibility/order. |
| 403 | `api_project_since_last_meeting` — `GET /api/projects/{project_id}/since-last-meeting` | `ProjectService.since_last_meeting(principal, project_id)` | High — preserve the current boundary timestamp and aggregate inputs. |
| 417 | `api_project_summary` — `GET /api/projects/{project_id}/summary` | `ProjectService.summary(principal, project_id)` | Medium — retain summary derivation and empty-project behavior. |
| 427 | `api_project_action_items` — `GET /api/projects/{project_id}/action-items` | `ProjectService.list_action_items(principal, project_id)` | Medium — preserve association/filter/status ordering. |
| 456 | `api_project_artifacts` — `GET /api/projects/{project_id}/artifacts` | `ProjectService.list_artifacts(principal, project_id)` | Medium — retain artifact provenance/visibility and ordering. |

### `holdspeak/web/routes/projections.py`

| Line | Handler and route | Service call | Complexity |
| --- | --- | --- | --- |
| 21 | `api_list_projections` — `GET /api/projections` | `ProjectionService.list(principal)` | Low — preserve visible projection ordering and state shape. |
| 49 | `api_set_projection_presentation` — `PUT /api/projections/{projection_id}/presentation` | `ProjectionService.set_presentation(principal, projection_id, state)` | Medium — validate state, access, and durable update semantics. |

## Implementation steps

1. Read the full projects and projections modules, then trace persistence and
   helper calls for each map row. Group shared project lookup/authorization
   inside the service so list/get/mutate/read models cannot drift.
2. Define typed patch/input DTOs only where needed to remove ambiguous raw JSON;
   preserve all existing request/response schemas.
3. Move project CRUD first, then resources/relationships and meeting links,
   then derived views. Ensure all mutations are transactionally grouped with
   the same integrity checks and failure semantics as today.
4. Move `since_last_meeting` and summary composition intact. Do not have the
   route collect inputs and ask a service merely to format them.
5. Move projection state validation and persistence into `ProjectionService`.
6. Wire services in the composition root. Replace every route body with
   parsing, one service call, service-error mapping, and serialization. Add
   direct service tests plus route shape/status regression tests.

## Acceptance criteria

- [ ] `ProjectService` owns every audited projects handler and every public
      operation accepts an explicit `Principal`.
- [ ] CRUD, archive, briefings, resource relationships, meeting associations,
      summaries, action items, artifacts, and since-last-meeting behavior
      retain current authorization, persistence, ordering, and response
      semantics.
- [ ] `ProjectionService.list` and `set_presentation` own both projection
      handlers, including validation and durable presentation state behavior.
- [ ] Project relationship and meeting-link mutations validate both sides and
      retain current idempotency/conflict behavior.
- [ ] Neither route module accesses the database, performs authorization or
      persistence, nor imports service-private persistence helpers.
- [ ] Service modules import neither FastAPI, `WebContext`, nor routes.
- [ ] Focused project/projection route and service tests plus
      `uv run pytest -q` pass.

## Builder verification

```bash
rg -n "class (ProjectService|ProjectionService)|def (list_projects|create_project|get_project|update_project|archive_project|list_briefings|list_resources|associate_meeting|since_last_meeting|set_presentation)" holdspeak/services
! rg -n "get_database\(|ctx\.get_database" holdspeak/web/routes/projects.py holdspeak/web/routes/projections.py
! rg -n "holdspeak\.web\.routes|WebContext|fastapi" holdspeak/services/project_service.py holdspeak/services/projection_service.py
uv run pytest -q
```

## Files in scope

- New: `holdspeak/services/project_service.py`
- New: `holdspeak/services/projection_service.py`
- `holdspeak/web/routes/projects.py`
- `holdspeak/web/routes/projections.py`
- Composition/context wiring that injects both services
- Related project, projection, relationship, meeting-association, route, and
  service tests
