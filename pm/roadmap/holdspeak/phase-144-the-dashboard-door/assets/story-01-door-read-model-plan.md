# HS-144-01 — The Door read model: implementation plan

**Planning baseline:** `feat/hs144-01-door-read-model`, read 2026-08-27. This plan implements only the server read model and its MCP twin. It does not alter the Chair or any other glass: **zero files under `web/src/` are in this story's law.** The settled Phase 144 design in `current-phase-status.md` §1–§5 is accepted as input, not reopened.

## Guardrails

- `GET /api/door` is one JSON-ready application projection, not a browser composition and not a second implementation of Follow-Through lane rules.
- The service composes the production `FollowThroughService`, the existing `RefinementThoughtService` unfinished projection, and `db.scheduled_recordings`; it does not query `action_items`, `cadence_loops`, People data, or `scheduled_recordings` through replacement SQL.
- All new proof fixtures construct real `Database`, `FollowThroughService`, `RefinementThoughtService`, `ScheduledRecordingService`/repository, `DoorService`, FastAPI router, and MCP JSON-RPC objects. A principal-setting HTTP middleware is the sole permitted wire fake. No decorated fake of a Door dependency is allowed.
- Every command that can load a DB, including the manifest generator and MCP walk, runs from repository root with `HOME="$(mktemp -d)" uv run --python 3.13.11 ...`. Do not use bare `uv`; it selects Python 3.14 here.
- The final source census, static no-schema/no-web proofs, API manifest generation, and MCP inventory-anchor update happen **after** functional focused proofs have passed and their output has been read. They never pre-bless an implementation.

## 1. Obligation register

| Acceptance obligation | Discharging slice(s) | Production proof |
| --- | --- | --- |
| `GET /api/door` returns `board`, `upcoming`, and `counts` together; every board card names its source, target ref, and lawful verbs. | S1, S2 | `tests/unit/test_door_read_model.py` asserts the complete JSON contract from real source objects; `tests/unit/test_door_routes.py` calls the assembled FastAPI route. |
| The original four Follow-Through lanes remain its authority, with unfinished Thoughts added only as `board.active`. | S1 | A composition-spy-free real-object fixture puts action/loop data in the four existing lanes and active Thoughts in `active`; assertions prove the service delegates lane projection to `FollowThroughService.board()` rather than reproducing lane logic. |
| Active Thoughts carry existing continuity labels/fields only; no `refinement_thoughts` schema extension occurs. | S1, S4 | `tests/unit/test_door_read_model.py` creates working Thoughts through the existing service and verifies their continuity/state/revision fields. The final evidence includes the bounded schema-block grep described in S4; the diff must contain no schema edit. |
| `counts` are server-computed and equal the lanes/timeline they summarize, including a generated fixture set. | S1 | A deterministic generated matrix of real action/Thought/schedule fixtures asserts `overdue`, `now`, `waiting`, `active`, and `upcoming_today` against the returned board/timeline—not a client recomputation. |
| Enabled scheduled recordings enter one ordered future timeline by `next_fire_at`, using a calendar-ready event shape. | S1 | Real repository records cover disabled, null-next-fire, past, future-today, and future-later schedules; `upcoming` is stable-ordered and contains only qualifying rows. |
| `door.get` is a closed MCP twin over the same `DoorService.get()` method as HTTP; HTTP/MCP agree on production compositions. | S3 | `tests/unit/test_door_mcp.py` covers discovery/closed schema; `tests/unit/test_door_transport_parity.py` drives separate fresh real HTTP and MCP sides through `server.handle_message()` and normalizes only generated timestamps/IDs. |
| No product glass changes occur under `web/src/`. | S4 | Final `git diff --name-only "$BASE"...HEAD` check has no `web/src/` path. No web client call is added, so the regenerated route is initially correctly labelled “server only.” |
| Existing route/MCP inventories stay truthful after adding one HTTP route and one tool. | S4 | Regenerate `docs/api-surface.json` and `docs/API_SURFACE.md`; update and run the exact MCP walk count; run `tests/unit/test_api_surface.py` and every existing MCP catalogue guard in the cross-cutting net. |

## 2. Verified live inventory

Audit A was produced from `main` only hours earlier. The relevant source anchors below were rechecked against this branch; all code anchors remain live. The only dirty files in this checkout before planning are the story/status Markdown files, not the product anchors.

### Read-model sources

| Concern | Live source and verified anchor | Build implication |
| --- | --- | --- |
| Existing four-lane authority | `holdspeak/services/follow_through_service.py:103-105` defines terminal states and the four lanes; `:122-236` computes `now`, `waiting`, `unassigned`, and `overdue` over actions, loops, decisions, and the People overlay. | `DoorService` calls `FollowThroughService.board(principal)` once and adapts the returned cards. It must not copy `_lane`, `_action_rows`, `_loop_rows`, or People projection logic. Audit A’s `:104-231` anchor is still accurate. |
| Follow-Through card facts | `follow_through_service.py:63-86` declares source, lane, provenance, and optional `target_ref`; helpers route only terminal filtering and lane placement at `:468-562`. | Preserve source/provenance facts; add Door-owned target refs and verb descriptors only at the aggregate boundary. |
| Thought persistence is fixed | `holdspeak/db/schema.py:859-883` is precisely the `refinement_thoughts` definition and its resume index. It has state/revisions/continuity revision/resume order, and no owner/due/priority column. | No migration and no `schema.py` edit. Audit A’s anchor has no drift. |
| Existing unfinished-Thought read truth | `holdspeak/services/refinement_thought_service.py:272-295` supplies the keyset-paged `state='working'` projection; `:1712-1720` turns it into title/preview/continuity fields. The HTTP adapter is `holdspeak/web/routes/primitives/thoughts.py:68-80`. | Iterate the existing bounded projection to exhaustion at service level; do not recreate its continuity query. |
| Chair’s present caller | `web/src/desk/thoughts.ts:248-265,450-452` declares/calls `unfinishedThoughts`; `web/src/desk/chair/FinishThoughtsLane.tsx:45-60,75-93` consumes it. | This is evidence for the field contract only. S1 changes none of these files. Audit A’s `FinishThoughtsLane.tsx:45-60` anchor still contains the fetch path. |
| Scheduled recording persistence | `holdspeak/db/schema.py:3354-3375` defines the table and enabled/`next_fire_at` index; `holdspeak/db/scheduled_recordings.py:15-120` supplies `ScheduledRecording`, `list_enabled()`, and raw epoch timestamps. | Compose `db.scheduled_recordings.list_enabled()`; filter missing/past `next_fire_at` in the Door projection and serialize at its boundary. Audit A’s schema anchor is exact. |
| Existing scheduled read adapter | `holdspeak/services/scheduled_recording_service.py:138-157` uses the repository list; `holdspeak/web/routes/scheduled_recordings.py:55-64` exposes its list route. | The Door uses the store as required, not HTTP or a reimplemented table query. Existing list behavior remains in the test net. |

### Registration, parity, and generated guards

| Concern | Live source and verified anchor | Required change / guard |
| --- | --- | --- |
| HTTP route registry | `holdspeak/web/routes/__init__.py:13-50,52-90` imports/exports route factories. `holdspeak/web_server.py:591-630` imports them and `:830-917` mounts them; Follow-Through is mounted at `:833`, scheduled recordings at `:915`. | Add `build_door_router` to both registries and mount one `/api/door` router. |
| Process composition | `holdspeak/web/context.py:18-109` carries composed application services; `holdspeak/web_server.py:760-785` constructs `FollowThroughService` (with the production People projection) and refinement application service. | Add one `door_service` context field and compose it once at server startup from the already composed Follow-Through service plus real thought/scheduled dependencies. |
| MCP family dispatch | `holdspeak/mcp/families/__init__.py:18-37` is canonical family import/order. `holdspeak/mcp/tools.py:420-423` builds `TOOLS`; `:450-460,522-547` validates and dispatches by family membership. `holdspeak/mcp/server.py:68-110` is the actual tools/list and tools/call protocol boundary. | Add a dedicated `door` family with only `door.get`, then register it in `FAMILIES`; do not put another special-case into the legacy monolithic `tools.py` dispatch. |
| Phase 143 parity precedent | `holdspeak/mcp/families/model_library.py:161-169,219-273` and `inference_assignments.py` compose application services; `tests/unit/test_phase143_transport_parity.py:40-92,204-337` creates independent real HTTP/MCP sides and compares declared vectors through `TestClient` and `server.handle_message`. | Copy the mechanism, not its model-domain fixtures: a new Door parity file compares `DoorService.get()` output through both transports. |
| API manifest | `scripts/gen_api_surface.py:32-33,46-77,203-215,259-269` discovers the real assembled app and writes both manifest artifacts. `tests/unit/test_api_surface.py:37-62` makes both snapshots fail-closed. | After behavior is proven, run `HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/gen_api_surface.py`, review its one-route diff, then run the API guard. It should show `GET /api/door`, initially server-only. |
| MCP count/anchor guards | `scripts/mcp_walk.py:181-218` currently hard-codes `tool_count_134` and resource counts. `docs/MCP_SIDECAR.md:3-5,57-60` and `README.md:443-464` claim 134 tools; all existing `tools/list` guard files are named in §5. | One new tool makes the exact tool count 135. Update the MCP walk assertion/name and the two prose inventory anchors only as the final inventory act; do not change resource counts or add a resource. The walk is run with `HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/mcp_walk.py`. |

## 3. Contract decided for implementation

The wire shape is deliberately version-free at this established HTTP seam, while the MCP tool schema is versioned (`holdspeak://mcp/door.get@1`). `DoorService.get(principal)` returns a JSON-ready dictionary directly; neither transport has a second serializer.

```json
{
  "board": {
    "now": ["<follow-through card>"],
    "waiting": ["<follow-through card>"],
    "unassigned": ["<follow-through card>"],
    "overdue": ["<follow-through card>"],
    "active": ["<working-thought card>"]
  },
  "upcoming": ["<timeline item>"],
  "counts": {
    "overdue": 0,
    "now": 0,
    "waiting": 0,
    "active": 0,
    "upcoming_today": 0
  }
}
```

A Follow-Through card retains its source facts (`id`, `source`, `text`, `owner`, `due`, `status`, `stale_score`, and `provenance`) and adds:

```json
{
  "target_ref": "action_item:action-17",
  "lawful_verbs": [
    {"name": "follow_through.complete", "arguments": {"card_id": "action-17", "verb": "done"}}
  ]
}
```

The legal vocabulary is data, not a new write route: active action cards may name `follow_through.complete` with `done`, `dismiss`, `snooze` (requiring `payload.until`), or `delegate` (requiring `payload.to`); active cadence/decision-loop cards name `cadence.set_status` with `closed` or `killed`; active People cards name `people.commitment.transition` with `done` or `dismiss`. Terminal-only/no-op `reopen` is not advertised on an already-active card. The descriptor’s `target_ref` is the actual native write target (`action_item:…`, `cadence_loop:…`, or existing People ref), so `source: "decision"` does not falsely claim a decision itself is mutable.

An active Thought card is deliberately different only where the existing aggregate is different:

```json
{
  "id": "thought-17",
  "source": "thought",
  "target_ref": "thought:thought-17",
  "open_ref": "note:note-17",
  "title": "Untitled thought",
  "body_preview": "…",
  "state": "working",
  "continuity_state": "review_ready",
  "updated_at": "…",
  "aggregate_revision": 3,
  "lifecycle_revision": 2,
  "filing_status": "filed",
  "lawful_verbs": [
    {
      "name": "thought.complete",
      "arguments": {
        "thought_id": "thought-17",
        "expected_aggregate_revision": 3,
        "expected_lifecycle_revision": 2
      },
      "required_arguments": ["request_id"]
    }
  ]
}
```

`upcoming` is a future, ordered timeline contract ready for HS-144-02:

```json
{
  "id": "sr_17",
  "source": "scheduled_recording",
  "target_ref": "scheduled_recording:sr_17",
  "title": "Daily standup",
  "starts_at": "2026-08-27T14:00:00Z",
  "ends_at": "2026-08-27T14:30:00Z",
  "location": null,
  "meeting_url": null,
  "state": "idle"
}
```

`starts_at`/`ends_at` are UTC ISO-8601 instants. For a scheduled recording, `ends_at` is `next_fire_at + duration_minutes`; calendar projections in Story 02 can emit this same shape with `source: "calendar_event"`, location, and meeting URL without changing the glass contract. Include only enabled records with a non-null `next_fire_at >= now`, sorted by `(starts_at, source, id)` for deterministic ties.

Counts are calculated once in the service from the returned projection: lane lengths for `overdue`, `now`, and `waiting`; active-card length for `active`; and timeline items with `starts_at` in the local server civil interval `[today 00:00, tomorrow 00:00)` for `upcoming_today`. The instant and local timezone are captured once per call. `unassigned` remains a board lane but is intentionally not a claimed headline count because the charter names exactly the five count keys above.

## 4. Ordered implementation slices

### S1 — Compose the Door projection from present authorities

**Create**

- `holdspeak/services/door_service.py`
- `tests/unit/test_door_read_model.py`

**Edit**

- `holdspeak/web/context.py` — add a typed/optional `door_service` composition slot.
- `holdspeak/web_server.py` — compose the one production `DoorService` using the existing context-owned `FollowThroughService` (including its People projection), `RefinementThoughtService`, and `get_database().scheduled_recordings` repository; place it on `WebContext`.

**Implementation details**

1. Define `DoorService.get(principal) -> dict[str, Any]` and small private adapters only. Inject its three production collaborators plus a narrow clock seam for deterministic time tests; do not give it a SQL query for Follow-Through, Thought, or schedule selection.
2. Call `follow_through_service.board(principal)` once; adapt four returned lists into the established order and append separately projected working Thoughts as `board.active`. Iterate `RefinementThoughtService.list_unfinished(principal, limit=50, cursor=...)` to exhaustion so `counts.active` never silently becomes “first page only.”
3. Map source-aware `target_ref` and `lawful_verbs` exactly as contract §3 specifies. Preserve provenance rather than reducing it to guessed text. Do not add a Door write endpoint or a schema column.
4. Call `scheduled_recordings.list_enabled()` once. Filter non-future/null records in the aggregate, calculate schedule end time from existing `duration_minutes`, serialize UTC ISO instants, and sort the one timeline. Calendar is not queried or stubbed.
5. Build counts from the completed response structure—not independent SQL count queries—so a hidden/snoozed card cannot make the headline disagree with what Door returns.

**Named proofs**

- `tests/unit/test_door_read_model.py::test_door_projection_composes_real_follow_through_thought_and_schedule_objects`
- `tests/unit/test_door_read_model.py::test_active_thoughts_keep_existing_continuity_and_only_lawful_complete_verb`
- `tests/unit/test_door_read_model.py::test_counts_equal_returned_lanes_and_today_timeline_over_generated_fixture_matrix`
- `tests/unit/test_door_read_model.py::test_upcoming_filters_and_orders_enabled_next_fire_records_with_calendar_ready_shape`
- `tests/unit/test_door_read_model.py::test_door_never_needs_refinement_thought_schema_fields_beyond_existing_projection`

The fixture creates a real owner principal, actual working Thoughts, actual follow-through actions/loops, and actual schedule repository rows. It must not monkeypatch `FollowThroughService.board`, the thought service, or the scheduled repository.

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_door_read_model.py \
  tests/unit/test_follow_through_service.py \
  tests/unit/test_walk_follow_through_125.py \
  tests/unit/test_scheduled_recording_conductor.py --tb=short
```

### S2 — Expose exactly one HTTP aggregate route

**Create**

- `holdspeak/web/routes/door.py`
- `tests/unit/test_door_routes.py`

**Edit**

- `holdspeak/web/routes/__init__.py`
- `holdspeak/web_server.py` — import and mount the new factory once, adjacent to the existing read-model routers.

**Implementation details**

1. `build_door_router(ctx)` exposes only `GET /api/door`. It obtains `ctx.door_service`, takes the request principal using the established route idiom, and returns `service.get(principal)` without reconstructing board/timeline/count dictionaries.
2. Isolated route tests inject a real, fully composed `DoorService` through `WebContext`; production startup owns the production composition. Do not make the route import the raw DB or assemble a shadow Follow-Through service.
3. Preserve established service-error-to-HTTP grammar if the existing thought owner authority refuses. The route takes no filters: it is the one front-door aggregate, not an alternate Follow-Through API.
4. No `web/src` client is introduced. The later glass story will consume this route and will be the next manifest consumer change.

**Named proofs**

- `tests/unit/test_door_routes.py::test_get_door_returns_one_complete_aggregate_from_real_service`
- `tests/unit/test_door_routes.py::test_get_door_carries_existing_thought_authority_refusal`
- `tests/unit/test_door_routes.py::test_route_does_not_replace_follow_through_or_schedule_authorities`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_door_read_model.py \
  tests/unit/test_door_routes.py \
  tests/unit/test_follow_through_service.py \
  tests/unit/test_scheduled_recording_routes.py --tb=short
```

### S3 — Add the closed `door.get` twin and reciprocal parity proof

**Create**

- `holdspeak/mcp/families/door.py`
- `tests/unit/test_door_mcp.py`
- `tests/unit/test_door_transport_parity.py`

**Edit**

- `holdspeak/mcp/families/__init__.py` — import/register `door` in canonical `FAMILIES` order.

**Implementation details**

1. Define exactly one no-argument, recursively closed `door.get` schema with `$id: holdspeak://mcp/door.get@1`. Its dispatcher calls `_service().get(principal)` and nothing beneath it.
2. The family’s `_service()` constructs the same `DoorService` production composition pattern as HTTP, rather than returning a hand-made dict or calling individual repositories. Its real Follow-Through construction preserves the same People projection policy as the HTTP app; see [ORCH-CALL] 6.
3. Follow the Phase 143 parity harness shape in a Door-specific test: separate fresh `Database` objects, separate composed `DoorService` instances, an actual FastAPI `TestClient` side, and `mcp.server.handle_message()` on the MCP side. Seed both using real services/repositories. Fake only HTTP request principal injection and `server.resolve_auth`.
4. Compare the entire logical response. The normalizer may replace generated IDs and current timestamps by structural role only; it must retain source, target refs, legal verbs, continuity state, lane order, counts, scheduled event shape, HTTP status, and MCP `isError` facts.

**Named proofs**

- `tests/unit/test_door_mcp.py::test_door_get_is_discoverable_with_a_closed_versioned_schema`
- `tests/unit/test_door_mcp.py::test_door_get_dispatches_the_real_door_service`
- `tests/unit/test_door_transport_parity.py::test_door_get_http_and_mcp_parity_on_fresh_production_compositions`
- `tests/unit/test_door_transport_parity.py::test_door_get_owner_refusal_matches_across_transports`

**Focused command**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_door_mcp.py \
  tests/unit/test_door_transport_parity.py \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_follow_through_mcp.py \
  tests/unit/test_scheduled_recording_mcp.py --tb=short
```

### S4 — Final source census and generated inventory truth

**Create:** none.

**Edit only after S1–S3 output is green and read**

- `scripts/mcp_walk.py` — `tool_count_134` becomes a clearly named `tool_count_135`; add a narrow `door.get` protocol assertion if the existing walk’s family exercises support it.
- `docs/api-surface.json` and `docs/API_SURFACE.md` — generated by `scripts/gen_api_surface.py`, never hand-edited.
- `docs/MCP_SIDECAR.md` and `README.md` — revise their MCP inventory count from 134 to 135 and add the concise one-tool Door family inventory anchor. Do not repair unrelated resource-count history in this story.

**Proof and regeneration sequence**

1. Capture the no-schema extension proof (the `!` is expected success only when the bounded table block has no forbidden new planning fields):

```bash
HOME="$(mktemp -d)" bash -lc '
  rg -n -A24 "^CREATE TABLE IF NOT EXISTS refinement_thoughts" holdspeak/db/schema.py
  ! rg -n -A24 "^CREATE TABLE IF NOT EXISTS refinement_thoughts" holdspeak/db/schema.py | rg -n "\\b(owner|due|priority)\\b"
'
```

2. Capture the no-glass proof against the branch base selected by the builder:

```bash
BASE="$(git merge-base HEAD origin/main)" \
  git diff --name-only "$BASE"...HEAD | rg '^web/src/' && exit 1 || test ${PIPESTATUS[0]} -eq 1
```

If the branch is not tracking `origin/main`, substitute its recorded story-base SHA; do not use the absent output as permission to change `web/src`.

3. Regenerate the manifest as the last API-source act, then inspect the diff before the test:

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/gen_api_surface.py
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/unit/test_api_surface.py --tb=short
```

4. Recount/update the MCP documentation anchors and run the actual protocol count guard, again under an isolated home:

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 python scripts/mcp_walk.py
```

**Focused final net**

```bash
HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_door_read_model.py \
  tests/unit/test_door_routes.py \
  tests/unit/test_door_mcp.py \
  tests/unit/test_door_transport_parity.py \
  tests/unit/test_api_surface.py \
  tests/unit/test_mcp_tools.py --tb=short
```

Do not run the full suite for this story worker. The builder/orchestrator owns broader verification after the focused output is read.

## 5. Cross-cutting net — existing tests and guards that must run

The story is additive, but it shares composed readers, MCP catalogue state, and the live app route table. These are not optional “unrelated” tests.

### Follow-Through board consumers

- `tests/unit/test_follow_through_service.py` — canonical four-lane math, filters, snoozes, provenance, and date movement.
- `tests/unit/test_walk_follow_through_125.py` — real board/MCP walk and ledger behavior.
- `tests/unit/test_follow_through_mcp.py` — current board tool/resource surface.
- `tests/unit/test_write_through_verbs.py` — returned cards are later acted on by existing write verbs.
- `tests/unit/test_people_service.py` and `tests/unit/test_people_no_leaks.py` — the production Follow-Through instance can include an encrypted People overlay, so no aggregate may bypass/redact incorrectly.

### Scheduled-recording list consumers

- `tests/unit/test_scheduled_recording_routes.py` — HTTP create/list/get/update/delete plus ISO `next_fire_at` serialization.
- `tests/unit/test_scheduled_recording_mcp.py` — MCP list semantics and current catalogue membership.
- `tests/unit/test_scheduled_recording_conductor.py` — the conductor is the authority that changes enabled/state/`next_fire_at`; a Door projection must not make its state assumptions false.

### MCP catalogue/inventory consumers

Every existing `tools/list` guard must remain in the net: `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_phase133.py`, `tests/unit/test_mcp_phase133_ask.py`, `tests/unit/test_mcp_phase133_cadence.py`, `tests/unit/test_mcp_phase133_coder_memory.py`, `tests/unit/test_mcp_phase133_plugin_job.py`, `tests/unit/test_mcp_thoughts.py`, and `tests/unit/test_scheduled_recording_mcp.py`. `scripts/mcp_walk.py` is the sole exact 134→135 count guard; `scripts/desk_walk/walk_mcp_123.py` also has the lower-bound catalogue assertion and should be run if the MCP walk is run in the builder’s broader pass.

### App/API manifest consumer

- `tests/unit/test_api_surface.py` — fail-closed manifest and generated Markdown snapshot guard. It must run after, never before, the API manifest regeneration.

## 6. [ORCH-CALL]s with recommendations

1. **[ORCH-CALL] Door service location and composition — recommend `holdspeak/services/door_service.py` with a `DoorService` composed at the web application edge and in a matching MCP family factory.** It is a domain read model, not a web route helper or a new repository. Its only data authorities are injected `FollowThroughService`, `RefinementThoughtService`, and `ScheduledRecordingRepository`; this makes the HTTP and MCP call the same `get()` method and prevents duplicate lane/store queries.

2. **[ORCH-CALL] Aggregate shape — recommend the exact `{board, upcoming, counts}` shape in §3, with five ordered board keys and the common `source`, `target_ref`, and `lawful_verbs` card contract.** Use UTC ISO instants plus nullable `location`/`meeting_url` in `upcoming` now, so HS-144-02 can add `calendar_event` rows without a glass-side merge or a shape migration. Keep Follow-Through’s fact fields and Thought’s custody/revision fields; do not normalize away information or add invented owner/due/priority.

3. **[ORCH-CALL] Active Thought verbs — recommend active (`state='working'`) Thought cards advertise only `thought.complete`, with its existing revision fields prefilled and `request_id` explicitly required at execution time.** It maps to `POST /api/thoughts/{thought_id}/complete` and MCP `thought.complete`. `thought.resume` maps to `POST /api/thoughts/{thought_id}/resume` and MCP `thought.resume`, but is lawful only for a completed Thought (`refinement_thought_service.py:1279`); completed Thoughts are not in `active`, so advertising Resume there would be a false transition. `open_ref` is a presentation target, not a fake Resume verb.

4. **[ORCH-CALL] Count meaning and “today” boundary — recommend precisely five counts, with `upcoming_today` derived from returned future timeline items in one captured local server civil-day interval `[today midnight, next midnight)`.** Do not include `unassigned` in the headline object, do not count disabled/null/past schedules, and do not let the browser select its timezone/count algorithm. The server’s local boundary is honest today and can be replaced by a declared owner timezone only when such a source exists.

5. **[ORCH-CALL] MCP exposure — recommend one closed `door.get` tool in a new `door` MCP family and no `holdspeak://door` resource in HS-144-01.** The tool is the required parity twin; a resource would create a second discoverable reader/refresh contract without a charter requirement. Existing individual resources remain untouched. This changes the tool count 134→135 and no resource count.

6. **[ORCH-CALL] People-overlay disclosure parity — recommend that the Door’s common composition preserve the existing Follow-Through People overlay only when the caller’s transport has the same authorized People capability; never silently substitute a plaintext/decorated People fake.** HTTP uses its already composed production People service. MCP uses the existing People family’s capability/store construction and respects `HOLDSPEAK_MCP_PEOPLE_ACCESS`; when disabled/unavailable, the projection follows the existing Follow-Through safe-empty behavior rather than exposing commitment text. The reciprocal parity fixture contains no People row (therefore compares the ordinary common projection exactly), while a focused Door test proves disabled/unavailable People cannot leak or crash the aggregate. This is the only lawful way to reconcile exact application-method parity with the pre-existing encrypted disclosure boundary.

## 7. Risks and stop signals

| Risk | Containment / stop signal |
| --- | --- |
| Door copies Follow-Through lane math or bypasses the People projection. | Stop if S1 contains action/loop SQL or a second `_lane` implementation. Use the injected Follow-Through service and run the People/board net. |
| Active count lies after 20/50 Thoughts. | Stop if `list_unfinished` is called only once. Consume its cursor to exhaustion under the stable high-water contract. |
| A working Thought advertises Resume. | Stop if `lawful_verbs` contains `thought.resume` for an `active` card; it is a completed-only transition. |
| Scheduled timeline includes impossible/old records or forces a calendar-specific shape. | Stop on disabled/null/past `next_fire_at` rows in `upcoming`, a client-side merge, or a missing `ends_at`/nullable location/url shape. |
| HTTP and MCP compare fakes, or transport serializers drift. | Stop if either test side bypasses FastAPI/MCP JSON-RPC or mocks Door/Follow-Through/Thought/schedule services. Only principal/auth injection is a wire fake. |
| The added route/tool leaves generated truth stale. | Stop if the manifest does not show exactly the new server-only GET route, `mcp_walk.py` still asserts 134, or MCP docs/README still claim 134. Regenerate/review last, then rerun guards. |
| Scope creeps into the Chair. | Stop on any `web/src/` path in the diff. HS-144-03/04 own all glass. |

## 8. Orchestrator dispositions (ruled 2026-08-27)

All six [ORCH-CALL]s are ACCEPTED as recommended:

1. **ACCEPTED.** `holdspeak/services/door_service.py`, composed at the
   application edge, injected authorities only.
2. **ACCEPTED.** The §3 `{board, upcoming, counts}` shape is the
   contract; UTC ISO instants; calendar-ready timeline rows so
   HS-144-02 joins without a shape migration.
3. **ACCEPTED, and it amends the story text.** Active Thought cards
   advertise `thought.complete` only; `thought.resume` is
   completed-only (`refinement_thought_service.py:1279`) and never
   appears on an `active` card — the story's "resume/complete"
   phrasing is corrected by code truth, recorded here visibly.
4. **ACCEPTED.** Five counts; `upcoming_today` bounded to one captured
   server civil day. Single-user reality — a declared owner timezone
   waits for a source that exists.
5. **ACCEPTED.** `door.get` tool only, no resource; MCP inventory
   134→135 tools, docs count updated in HS-144-05.
6. **ACCEPTED.** The People encrypted-disclosure boundary is
   preserved exactly as recommended; the no-People parity fixture +
   the focused no-leak/no-crash test are both mandatory proofs.

Build proceeds S1→S2 (round 1), S3→S4 (round 2). Regens are the last
act of a round. No web/src changes; no schema changes.
