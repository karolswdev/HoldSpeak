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

Module: `holdspeak/project_contracts.py`
Tests: `tests/unit/test_project_contracts.py`

### Envelope shape (API-003, MCP-004)

Every Project write returns a `CommandResultEnvelope` with these fields:

| Field | Type | Requirement |
|-------|------|-------------|
| `result_kind` | `ResultKind` (closed enum) | API-003, MCP-004 |
| `project_id` | `str` (non-empty) | API-003 |
| `project_revision` | `int` (>= 0) | API-003, API-001 |
| `changed_refs` | `tuple[QualifiedRef, ...]` | API-003; validated through `holdspeak.refs` |
| `warnings` | `tuple[ProjectWarning, ...]` | API-003 |
| `errors` | `tuple[ProjectError, ...]` | API-003 |

### Result-kind vocabulary (16 values, closed)

| Value | SRS operation | Traceability |
|-------|---------------|--------------|
| `created` | project.create | SS11.1, SS10 project.created |
| `updated` | project.update | SS11.1, SS10 project.updated |
| `archived` | project.archive | SS11.1, SS10 project.archived |
| `restored` | project.restore | SS11.1, SS10 project.restored |
| `linked` | project.link | SS11.1, SS10 project.resource.linked |
| `unlinked` | project.unlink | SS11.1, SS10 project.resource.unlinked |
| `review_opened` | project.open_review | SS11.1, SS10 project.review.opened, SS7.2 |
| `proposal_decided` | project.decide_proposal | SS11.1, SS10 project.proposal.decided, SS7.3 |
| `review_accepted` | project.accept_review | SS11.1, SS10 project.review.accepted, DEL-005 |
| `update_drafted` | project.draft_update | SS11.1, SS10 project.update.drafted, UPD-001..003 |
| `update_saved` | project.update_draft (save) | SS11.1, UPD-005 |
| `update_published` | project.publish_update | SS11.1, SS10 project.update.published, UPD-005 |
| `steward_configured` | project.configure_steward | SS11.1, SS10 project.steward.configured |
| `steward_run_requested` | project.run_steward | SS11.1, SS10 project.steward.run_started, MCP-003 |
| `steward_stopped` | project.stop_steward | SS11.1, STW-003 |
| `no_change` | Idempotent replay | API-002 |

### Error-code table (5 values, closed)

| Code | Meaning | Requirement ID |
|------|---------|----------------|
| `stale_revision` | `expected_revision` does not match current; no partial mutation | API-001 |
| `idempotency_conflict` | Same `command_id`, different request hash | API-002 |
| `not_found` | Referenced Project or entity does not exist | SS6.3 (implied), DOM-001 |
| `validation` | Input fails structural or semantic validation | DOM-006, DB-004 |
| `capability` | Unsupported citizen mutation attempted | MCP-005 |

### ID-prefix table (SS4.1, 11 prefixes)

| Prefix | Entity | Stability | Generator signature |
|--------|--------|-----------|---------------------|
| `pitem_` | Project item | Stable for item lifetime | `generate_pitem_id() -> str` |
| `psrc_` | Source | Stable for one configured source | `generate_psrc_id() -> str` |
| `pobs_` | Observation | Deterministic | `generate_pobs_id(*, adapter, source_id, source_version, fact_key) -> str` |
| `pprop_` | Proposal | Deterministic | `generate_pprop_id(*, project_id, review_window_key, proposal_kind, target_ref, normalized_patch) -> str` |
| `prev_` | Review | Unique session identity | `generate_prev_id() -> str` |
| `pupd_` | Update | Stable draft identity | `generate_pupd_id() -> str` |
| `pchg_` | Change | Deterministic | `generate_pchg_id(*, project_id, project_revision, ordinal) -> str` |
| `pcmd_` | Command | Caller-supplied or generated once | `generate_pcmd_id() -> str` |
| `pstpol_` | Steward policy | Stable per Project policy | `generate_pstpol_id() -> str` |
| `pstrun_` | Steward run | Unique execution attempt | `generate_pstrun_id() -> str` |
| `pststep_` | Steward step | Unique step/effect attempt | `generate_pststep_id() -> str` |

ID format: `<prefix><32 hex chars>`. Non-deterministic IDs use
`uuid4().hex`; deterministic IDs use `sha256(length-prefixed inputs)[:32]`
-- both produce the same wire format. The deterministic generators take
keyword-only arguments matching the SS4.1 determinism inputs; same inputs
always produce the same ID.

Validators: `validate_<prefix>_id(id_str) -> bool` for each prefix, plus
`validate_id(id_str, prefix) -> bool` for the generic case.

---

## Room projection sections -- HS-158-04

Module: `holdspeak/services/project_service.py`
Route: `GET /api/projects/{project_id}/room`
Tests: `tests/unit/test_project_room_read.py`

### Section state vocabulary (SS6.2, NFR-006, Art VI)

Every section in the room projection carries a `state` field whose value
is drawn from this closed vocabulary:

| State | Meaning | Traceability |
|-------|---------|--------------|
| `ok` | Section read succeeded; data is present and current. | SS6.2 (per-section status) |
| `degraded` | Section read failed; sibling sections remain unaffected. Carries `error_code`. | NFR-003 (fault isolation), SS6.2 |
| `absent` | Domain not yet implemented. Carries `reason` explaining why. | Art VI (honest absence), NFR-006 (honest empty/stale/partial/failed/stopped) |

### Absent section shape

Sections whose backing domain does not yet exist use this exact shape:

```json
{"state": "absent", "reason": "not_yet_built"}
```

P1-absent sections: `review`, `sources`, `updates`, `steward`.

### Degraded section shape

When a sub-read raises an exception, the section degrades:

```json
{"state": "degraded", "error_code": "<section>_read_failed"}
```

The response remains HTTP 200; 404 only when the project itself is missing.

### Populated section shape

Each populated section carries `"state": "ok"` alongside its data fields.

### Focus ordering rule (DB-005)

The items focus block uses this deterministic ordering:

1. `severity DESC NULLS LAST` (items with severity before nulls; alphabetical descending within)
2. `due_at ASC NULLS LAST` (soonest due first; items without due last)
3. `sort_key ASC NULLS LAST`
4. `created_at ASC`
5. `id ASC` (unique tiebreaker -- fully deterministic)

### Caps (NFR-001, DB-005)

| Constant | Value | Controls |
|----------|-------|----------|
| `ROOM_FOCUS_CAP` | 5 | Maximum items in the focus block (WEB-NOW-006 spirit) |
| `ROOM_CHANGES_CAP` | 10 | Maximum recent changes |

True totals (by item_type and overall) accompany the capped focus list.

### observed_at determinism

`observed_at` is derived from `project.updated_at` (the DB-persisted
value), not from wall-clock time. Two consecutive reads with no writes
in between produce **byte-identical** payloads. This is the preferred
approach per the story spec.

### Requirement traceability

| Requirement | How satisfied |
|-------------|---------------|
| SS6.2 | One `GET .../room` returns header, focus, meetings, resources, changes, per-section status |
| NFR-001 | Focus and changes are bounded by named constants |
| NFR-002 | Items are deterministically ordered; changes are ordered by revision DESC |
| NFR-003 | Each sub-read is wrapped; failure degrades only its section |
| NFR-006 | Absent domains carry explicit `"state": "absent"` markers |
| Art VI | No empty-faked review/steward/update/sources payloads |
| API-006 | Legacy detail routes remain untouched |
| DB-005 | Reads are bounded, indexed, and deterministically ordered |
