# Project Rooms P0 -- the contract

Status: in-progress (HS-157)
Parent: SRS_DOMAIN_DRIVER.md

This document records the binding design decisions made during Phase
157 (The Contract). Each decision traces to a requirement ID from the
SRS and is backed by codebase evidence.

## Qualified refs (REF-001..004)

### Registered type table

The canonical type is the string that `format()` emits and that
`parse()` normalizes to. Aliases are accepted by `parse()` and
resolved to the canonical form; `format()` refuses them.

| Canonical type | SRS SS3.2 citizen       | Aliases    | Status  | Emission evidence |
|----------------|-------------------------|------------|---------|-------------------|
| `meeting`      | Meeting                 | --         | Active  | `holdspeak/db/projections.py:210,424,426,433,448,456,477,518,525,544,550`, `holdspeak/db/projects.py:228,245`, `holdspeak/meeting_session/intel_admission.py:187`, `holdspeak/meeting_session/transcribe_admission.py:188`, `holdspeak/meeting_session/intel_routed_children.py:121`, `holdspeak/services/monday_brief_service.py:308`, `holdspeak/services/meeting_deferred_queue_binding.py:168,229` |
| `decision`     | Decision                | --         | Active  | `holdspeak/db/decisions.py:127,576,667`, `holdspeak/services/monday_brief_service.py:497,507,539`, `holdspeak/services/follow_through_service.py:315` |
| `action_item`  | Door / follow-through   | `door`     | Active  | `holdspeak/services/door_service.py:163`, `holdspeak/db/projections.py:544`, `holdspeak/services/follow_through_service.py:315` |
| `people`       | Person / participant    | `person`   | Active  | `holdspeak/services/people_service.py:784,799`, `holdspeak/web/routes/people.py:329`, `holdspeak/mcp/families/people.py:317` |
| `thread`       | Thread                  | --         | Active  | `holdspeak/services/follow_through_service.py:477` (removeprefix), `web/src/desk/shell.ts:131`, `web/src/desk/surface/citations.tsx:33` |
| `note`         | Note                    | --         | Active  | `holdspeak/db/refinement_thoughts.py:237`, `holdspeak/services/refinement_thought_service.py:155,249,258,1252,1328,1343,1714` |
| `artifact`     | Artifact                | --         | Active  | `holdspeak/workbench_conductor.py:346`, `holdspeak/web/routes/delivery_prs.py:340`, `holdspeak/db/projections.py:468,470`, `holdspeak/db/decisions.py:127` |
| `workbench`    | Workbench               | --         | Active  | `holdspeak/services/workbench_service.py:456,491`, `holdspeak/services/workbench_runner.py:189,211,215,219,350`, `holdspeak/services/resourceful_service.py:279,282` |
| `agent`        | Agent / Recipe          | --         | Active  | `holdspeak/coder_factory.py:75` (`agent:tmux:name` identity pattern) |
| `watch`        | Watch                   | --         | Active  | `holdspeak/services/reaction_service.py:293,295,482,483` |
| `repo`         | Repo / delivery system  | --         | Planned | No emission evidence in codebase |
| `kernel`       | Kernel / Desk object    | --         | Planned | No emission evidence in codebase |

### Canonical-vs-alias ruling (REF-003): `people:` is canonical; `person:` is the alias

**Ruling:** The canonical person/participant ref type is `people`.
The alias `person` is accepted by `parse()` and resolved to `people`.
`format()` emits only `people:`.

**Rationale:** The existing codebase overwhelmingly uses `people:`.
Every emitter (6 sites) produces `people:`. Five of six parser sites
match `people:`. Only `holdspeak/services/thread_service.py:311`
parses `person:` (using `.startswith("person:")` then
`.split(":", 1)[1]`). The entire web desk -- `DoorBoardLane.tsx:432`
(emits), `PeopleCore.tsx:129` (parses) -- uses `people:`.

Making `person:` canonical would mean the new `format()` function
emits a form that only one existing consumer (thread_service) knows
how to match, while breaking the five consumers that match `people:`.
Making `people:` canonical means new code emits the form that all
existing consumers already handle.

The story's initial recommendation was `person:` (singular matches
`meeting:`, `decision:`). The linguistic consistency argument is
aesthetically valid but functionally dangerous: the runtime safety
argument wins. Existing emitters are out of scope for P0; they stay
as-is (all `people:`), and thread_service stays as-is (parses
`person:`). The central `parse()` function accepts both forms and
normalizes to `people`.

**Drift evidence:**

| Site | Form | Role |
|------|------|------|
| `holdspeak/services/people_service.py:784` | `f"people:{commitment['id']}"` | Emitter |
| `holdspeak/services/people_service.py:799` | `f"people:{commitment['relationship_id']}"` | Emitter |
| `holdspeak/web/routes/people.py:329` | `f"people:{commitment_id}"` | Emitter |
| `holdspeak/mcp/families/people.py:317` | `f"people:{commitment_id}"` | Emitter |
| `holdspeak/services/door_service.py:212` | `.removeprefix("people:")` | Parser |
| `holdspeak/services/people_service.py:807` | `.removeprefix("people:")` | Parser |
| `holdspeak/services/follow_through_service.py:40,362` | `.startswith("people:")` | Parser |
| `web/src/desk/chair/lanes/DoorBoardLane.tsx:432` | template literal `people:${...}:prep` | Emitter |
| `web/src/pages/cores/PeopleCore.tsx:129` | `.startsWith("people:")` | Parser |
| `holdspeak/services/thread_service.py:311` | `.startswith("person:")` | **Parser (sole `person:` site)** |

**Traceability:**

- REF-001: Central module at `holdspeak/refs.py`; fence test scans newly touched Project Rooms code.
- REF-002: Round-trip `parse -> format -> parse` for every registered type; tested in `tests/unit/test_project_refs.py`.
- REF-003: `people:` canonical, `person:` alias. Evidence table above.
- REF-004: Unknown types parse into `QualifiedRef` with `is_registered == False`; `format()` raises `UnregisteredTypeError`. Tested.

### Secondary alias: `door` -> `action_item`

The SRS SS3.2 names the citizen "Door / follow-through". The codebase
exclusively uses `action_item:` as the ref prefix (3 emission sites,
0 `door:` sites). Registered as alias for forward compatibility with
the SRS naming.

---

## Command results and errors -- HS-157-02

(Placeholder -- this section will be completed by story HS-157-02.)
