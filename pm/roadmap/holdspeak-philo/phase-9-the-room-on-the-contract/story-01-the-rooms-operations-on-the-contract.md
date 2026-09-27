# PHILO-9-01 - The Room's operations on the contract (and discovery)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter
- **Unblocks:** PHILO-9-02, PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F4, F6, F12, F13; the census table there; BACKLOG "Projects on the contract"
- **Canvas:** none (no face change)

## Problem

A client that knows only the catalogue cannot put a thing in a project: the only "add" verb is `project.add_suggested_source` (grounding F4); items and resources are HTTP only (`holdspeak/web/routes/projects.py:294-325`, `:411-515`). The face makes a project through the Door (`holdspeak/web/routes/project_door.py:4`) and MCP through `project.create`: two create paths. The Room read says the updates and the steward are `absent · not_yet_built` after both ran (`holdspeak/services/project_service.py:510-511`, F6). `desk.needs_you` counts muted projects on MCP and not on HTTP (`holdspeak/mcp/tools.py:1077-1090` vs `holdspeak/web/routes/projects.py:546-573`, F13). The descriptions name mechanisms, not his jobs (F12). The 18 MCP identities below are hand-wired (`holdspeak/mcp/families/project.py:1170-1414`, `holdspeak/mcp/tools.py:1077`).

## Scope

- **In:** explicit descriptors in `holdspeak/operations.py` for the 18 MCP identities of the charter's table (Room lifecycle 9, review 4, updates 4, `desk.needs_you` 1), bound at hub composition to the hub's `ProjectService`, `ProjectDeltaService` and `ProjectUpdateService`; the 3 HTTP constructors (`projects.py::_build_needs_you`, `automations.py::_project_service`, `people.py::projects`) reach the hub's services; new MCP exposure for the items (list, create, update, transition) and the resources (list, add, remove) over the same services; one create path (the Door's and `project.create` reach one operation, or the difference is a named field of one descriptor); the Room read reports the updates and the steward as they are; one needs-you count on both transports; descriptions and argument descriptions in his words (where each id comes from); the canonical names fixed in the first commit; a three-state compatibility table (base, round one, built) per operation; `docs/generated/operations.json` and the tool roster regenerated.
- **Out:** the steward, the nudges, the watches, the suggested sources and the connections (story 02); any face (story 03); the setup interview and the provider discovery tools (charter Out).

## Acceptance criteria

- [ ] The 18 MCP identities and the 3 HTTP identities leave the residual set (or MOVE with a named reason); the fence fails on a new residual identity on a copy of main.
- [ ] A client can list, create, update and transition an item, and list, add and remove a resource, over MCP; each reaches the same live service as the route in one hub; durable across a restart.
- [ ] The discovery fence reads only the real `tools/list` answer and maps "make a project", "add a milestone / risk to a project", "what needs me", "draft my update" and "send my update" to a tool and an argument path; red on main.
- [ ] `project.get_room` and `GET /api/projects/{id}/room` report a published update and a completed steward run (red on main: `not_yet_built`).
- [ ] With a muted project, `desk.needs_you` and `GET /api/desk/needs-you` give the same count (red on main).
- [ ] Existing names, arguments, envelopes and refusals are kept (the compatibility tables); palette refusal tested through dispatch.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days (the charter's estimate).

## Test plan

- **Unit/integration:** descriptor fences; the discovery fence over `tools/list`; the Room-read and needs-you fences through the real hub on an isolated HOME; `scripts/residual_census.py --check` on the branch and on a copy of main.
- **Rig:** `op` steps for each new operation via `/api/mcp`.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
