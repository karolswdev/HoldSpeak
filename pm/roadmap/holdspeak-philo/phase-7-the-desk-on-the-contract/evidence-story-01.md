# Evidence - PHILO-7-01

- **Story:** PHILO-7-01 - Notes and directories on the contract (and discovery)
- **Status:** done
- **Date:** 2026-09-25
- **Branch:** `feat/philo-7-01-notes-directories` from main `02a862f2`; the build commit `c572f37b`.

## What was built

- **The slice table** (`holdspeak/operations.py`): fifteen explicit descriptors, `NOTE_CREATE` (:633) to `KB_LIST` (:989): `note.create/read/update/delete/list`, `zone.create/read/update/delete/list`, `kb.create/read/update/delete/list`. Each names its real `PrimitiveService` method, a closed argument schema (names closed, values type-permissive, as the decision fields), result, refusals, exposure and completion. `DESK_OPERATIONS` (:1009) is the one (kind, verb) -> operation table the MCP tools, the `desk.verb` aliases and the resource read; `DESK_ID_ARGUMENT` (:1032) names each kind's id argument. No row resolves a callable from a kind string.
- **The admission, declared** (`Admission`, :79; the descriptor field :142; exported :167): every row carries its rule from the phase status's admission table — `exempt`, `admitted` (`zone.delete`), or `admitted_if` with the arguments the condition reads (`zone.create` `directory_id`; `zone.update` `parent_id`; `kb.create` `member_ids`, `kb_id`; `kb.update` `member_ids`; `note.delete` a Thought's note: stored state, no argument). Declared only; PHILO-7-02 enforces.
- **Thought-owned notes declared:** `note.update` and `note.delete` name the retry cursors in their result and `thought_expected_revision_required` / the Thought service's codes in their refusals; `note.create` names the refusal over a Thought's note id. Behaviour unchanged (`services/primitive_service.py:91-151` untouched).
- **Binding:** no composition change — `operations.bind` over `BOUND_SERVICES` already binds every `primitive_service` descriptor to the hub's one instance at composition (`runtime/composition.py:523-528`).
- **HTTP over `invoke`:** `web/routes/primitives/notes.py:51,61,78,90,110`, `directories.py:44,54,75,91,108`, `kbs.py:45,55,71,83,97`. The route `_svc()` fallback constructions are gone; the membership routes (story 02) use `_ops().target(...)`, the instance the contract is bound to (the Phase 5 decisions precedent).
- **MCP over `invoke`:** `mcp/tools.py:622-658` (`_desk_operation` and the five `_primitive_*` helpers read `DESK_OPERATIONS`); `desk.verb` desk.create/update/delete use the same helpers. Workflows, chains and `desk.delete kind=decisions` keep the generic path.
- **The resource:** `holdspeak://primitives/{kind}/{id}` reads through the declared read operation for decisions, notes, zones and knowledge bases (`mcp/resources.py:574`); workflows and chains keep the fresh service read.
- **The rig's `op` step:** the fifteen rows are in `scripts/graph_walk.py` `OP_MCP_PROJECTIONS` (:757-771) with their argument translation (`_DESK_OP_KINDS` :775); the reads are observation operations.
- **THE RENAME REPAIR:** `KBRepository.rename` (`db/primitives.py:434`) and `DirectoryRepository.rename` (`:1166`) write the name (and `last_modified`) and nothing else, on a live row; `PrimitiveService.update_kb` without `member_ids` and `update_directory` without `parent_id` call them (`services/primitive_service.py:273,381`). With `member_ids` / `parent_id` the ADMITTED path is unchanged (the upsert).
- **A defect found and repaired:** on main every `desk.*` zone call except `desk.list` (and every `desk.verb` zone alias) failed: `_KIND_ALIASES` stripped one letter ("directories" -> "directorie") and the getattr asked for `create_directorie` (main `holdspeak/mcp/tools.py:34`). The explicit rows and the corrected alias (`mcp/tools.py:38`) repair it. "Make a zone" over MCP never worked before this story.
- **DISCOVERY:** the descriptions of `desk.list/get/create/update/delete/verb`, `zone.file/unfile/list_members`, `kb.add_member/remove_member/list_members` name the jobs in plain words ("Find a note", "Read a note", "Make a zone", "File a note into a zone", "List the notes in a zone", "Put a decision on my review list" — the words only; story 02 pays the operation) and every id argument names its source tool ("from desk.list kind=directories"). Argument validation is unchanged: only `description` keys were added.
- **Shelf-enum alignment:** the MCP `monday_brief.shelf` `state` schema is now `{"type": ["string", "null"]}` with the three states in words (`mcp/tools.py:489`); an unknown state reaches the registry and the brief service refuses it ("Unknown shelf state: x"), the same refuser and text as HTTP. `brief.shelf.write` already declared that the service refuses; the declaration is now true on both transports.
- **Generated:** `docs/generated/operations.json` (32 operations, each with `admission`), `docs/generated/api-reference.json` (route lines; it already drifted on main — `philo_api_reference.py --check` red on the main copy), the roster `docs/MCP_SIDECAR.md` regenerated with no change (228 tools).

## Measurements (two, never one)

- **Residual identities** (`scripts/residual_census.py`, `docs/internal/philo/phase-5/residual-set.json`): **320 -> 293**. MCP **256 -> 232** (-24: identities 2-5, 7-24, 26-27); HTTP **64 -> 61** (-3: identities 34-36); route `*Service(...)` constructions 66 -> 63. The 27 are listed in the set's `paid` under `PHILO-7-01`.
- **34-36 are PAID, not moved:** the fallback construction left the three routes. The bare build a partially wired route test needs is the Phase 5 lawful case 3 in `operations._bare_primitives` (not a route module, so the census's counting rule does not count it — stated so no one reads the HTTP number as "no bare build anywhere").
- **Public MCP tools:** 228 -> 228 (no tool added).
- **Still residual (story 02's):** `desk.delete`/`desk.verb desk.delete` `kind=decisions` (#6, #25), `decision.supersede` (#1), the six membership tools (#28-33).

## The three-state compatibility tables (`tests/unit/test_philo7_compat.py`, imports nothing the story adds)

| Kind | Base main `02a862f2` | Round one = built `c572f37b` |
|---|---|---|
| notes (MCP create/update rows, get/list/delete/verbs envelopes, HTTP rows, the Thought's note revision rules) | green | green |
| kbs (the same) | green | green |
| zones, HTTP rows | green | green |
| zones, MCP rows (`test_zone_mcp_*`, 17) | RED by design: every row answered "'PrimitiveService' object has no attribute 'create_directorie' / 'update_directorie'" | green: the zone service's own outcome, the one HTTP gave on main for the same input |
| the primitive resource, every kind | green | green |

Totals: base main 61 passed, 17 failed (all 17 are the zone defect); built 78 passed. There is no separate round one: this is the first build and no check on built has bounced it yet; if one does, round two is recorded here.

**Every changed behaviour, stated in full:**

1. MCP zone writes and reads (`desk.create/get/update/delete kind=directories` and the `desk.verb` aliases) were refused on main by the `directorie` defect; they now reach the zone service. A widening.
2. The refusal TEXT for an unknown or misplaced field in `desk.create`/`desk.update` data for notes, zones and kbs: main a Python `TypeError` text ("unexpected keyword argument ..."; "multiple values for argument ..."), now `Invalid arguments for note.create: ...` (`invalid_arguments`); an authority field (`owner`, `actor` ...): main a `TypeError`, now `authority_in_arguments`. Refused in both; the same `isError` envelope. Unlike Phase 5's decisions nothing here was accepted-and-ignored, so there is no narrowing.
3. The shelf: an unknown state over MCP was refused by the transport schema ("Invalid arguments for monday_brief.shelf: state: 'filed' is not one of [...]"); it is now refused by the brief service ("Unknown shelf state: filed"). Still refused, still `isError`; the published `state` schema is `["string", "null"]` with the states in words instead of an enum. A non-string state is still refused before the registry on both transports. `tests/unit/test_philo5_the_loop.py:599-602` pinned the old text; it is updated.
4. The renames: sequentially identical. Under an interleaving the other action now survives (the fences below). Two edge effects of writing the name only, stated: (a) a rename of a knowledge base or zone deleted between the rename's read and its write now answers NotFound instead of resurrecting the row (the upsert set `deleted = 0`); (b) `kb.update` with neither `name` nor `member_ids` no longer rewrites the knowledge memberships from the legacy `member_ids_json` list (it did, whenever that list was fully qualified); it now moves `last_modified` only. A zone update with neither `name` nor `parent_id` likewise moves `last_modified` only.
5. The `holdspeak://primitives/decisions/{id}` resource reads through `decision.read` (in the hub, the hub's instance instead of a fresh service); same result. `decision.read` now lists that exposure.
6. Tool and argument DESCRIPTIONS changed (text only). Names, required arguments, defaults, envelopes, refusals and palette membership are unchanged (`test_published_desk_tool_schemas_are_unchanged_and_admit_every_contract_payload`, `test_mcp_phase133_surface.py` kind-boundary sentences, both green).
7. Authority: unchanged. No descriptor is `owner_only`; an agent and a node principal write through the contract as on main (`test_a_non_owner_principal_writes_as_it_did_on_main`). The Thought service's own owner check for a Thought's note is untouched.

## The fences and their reds (retained under `docs/internal/philo/phase-7/notes-and-directories/`)

`red-main-behaviour.txt`: the five new test files run UNCHANGED on a `git archive` copy of main `02a862f2` (isolated HOME): 65 failed, 70 passed. Counted behavioural reds (real producers, the real hub):

- **Rename interleaving** (`test_philo7_rename_repair.py`), 2 red: `AssertionError: the rename tombstoned the member added during it: ['note:a']`; `AssertionError: the rename reversed the move made during it: parent_id='p1'` — Astra's reproduction exactly. The pause is after the rename's own real `get`; the fence asserts the pause fired (it cannot pass empty).
- **Zone MCP** (`test_philo7_compat.py`), 17 red: `the zone call never reached the zone service: {'error': "'PrimitiveService' object has no attribute 'create_directorie'"}`.
- **Discovery** (`test_philo7_discovery.py`), 16 red: `'file a note into a zone' is named by [], expected ['zone.file']` (and the five other phrases); `zone.file.directory_id does not say where its value comes from: ''` (and every id argument). The fence reads only the real hub's `tools/list` answer.
- **Shelf alignment** (`test_philo7_shelf_alignment.py`), 1 red: `the MCP refusal never reached the registry: {'error': "Invalid arguments for monday_brief.shelf: state: 'filed' is not one of ['acknowledged', 'deferred', None]"}` (`assert [] == ['brief.shelf.write']`).
- **Both transports through `invoke`** (`test_philo7_contract.py`), 4 red: `assert [] == ['note.create', ... 'note.delete']`, the same for zones and kbs, and `assert [] == ['note.update', 'note.update']` for the Thought's note — the one registry never saw these calls on main.
- NOT counted: the contract file's other failures on main are `AttributeError`/`Unknown operation: note.read` (symbols the story adds).

`red-main-residual.txt`: `scripts/residual_census.py --check --root <main copy>` with the branch's set: `RESIDUAL FENCE RED: 27 problem(s)`, each a NEW residual identity — the 27 this story pays.

`red-mutations.txt`: deliberate mutations on the branch, each applied, its fence run, the file copied back (no git verb): m1 drop the (note, update) row -> `a slice operation has no (kind, verb) row`; m2 `zone.delete` admission -> exempt -> `('exempt', ()) == ('admitted', ())`; m3 `GET /api/notes/{id}` calls the service by hand -> the invoke recording misses `note.read`; m4 the primitive resource bypasses the contract -> the recording misses `zone.read`/`kb.read`; m5 remove the words "Find a note" -> `'find a note' is named by []`; m6 the kb rename writes the snapshot back -> the new member lost; m7 restore the MCP shelf enum -> the refusal never reaches the registry; m8 restore the `directorie` alias -> `no attribute 'create_directorie'`; m9 the zone rename takes the upsert path -> the move lost.

## Integration (the real `MeetingWebServer` hub)

- `test_every_slice_operation_is_bound_to_the_hubs_one_instance`: all fifteen `target(name) is root.primitive_service is ctx.primitive_service`; `for_runtime`/`for_context` return the one registry.
- `test_http_mcp_verbs_and_the_resource_all_go_through_invoke[notes|directories|kbs]`: HTTP create/read/update/list/delete, then MCP `desk.create/get/update/list`, the resource, and `desk.verb` create/update/delete plus `desk.delete` — every call recorded by the one registry's `invoke` in order.
- `test_a_thoughts_note_updates_through_both_transports_with_its_revisions`: HTTP `PUT /api/notes/{id}` with the cursors (working_revision +1), then MCP `desk.update` with the next cursors (+1 again), both `note.update`; a stale cursor refused `thought_revision_conflict`.
- `test_durable_state_survives_a_new_hub_over_the_same_database`: a note, a zone and a kb made over MCP on hub one, read over MCP and HTTP on hub two (a different registry and instance).

## Calibration (the charter's promise)

The estimate was 3-4 engineering days PROVISIONAL, to be calibrated after the first kind (notes). The three kinds were built together (one table), so there is no notes-only point. The whole story, in this lane: `dw story status ... in-progress` at 2026-09-25 12:18 MDT; the build commit `c572f37b` at 12:39 MDT (all fences red on main and green); the evidence and the records after. About 25 minutes of agent-lane wall-clock for code and fences, before Astra's check on built. Agent-lane minutes and engineering days are not the same unit; the honest reading is that story 01's size was dominated by reading and fence design, not code, and that the 3-4 d figure over-states this story for an agent lane. Rounds after Astra's check are not in this number.

## Not done, and uncertain

- Kernel admission and receipts: none added (story 02). The admission is declared only.
- Membership tools/routes (`zone.file/unfile/list_members`, `kb.*_member*`), `decision.delete/status/supersede`: not moved (story 02); only their descriptions changed (discovery).
- The discovery fence proves the words are in `tools/list`; it does not prove a model finds them (story 04).
- The shelf schema lost its `enum` (the words name the states). If the other brain prefers the enum kept and the contract to own the refusal instead, that is a one-line swap plus the descriptor's schema; not done here.
- Not run: the full suite (CI's job), the web vitest baseline (no web file touched), any browser case (story 03).

## Proof

### Captured run — 2026-09-25T18:40:34Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.N1KVLrxzof uv run pytest -q -n 8 -p no:cacheprovider tests/integration/test_hs165_mcp_walk.py tests/integration/test_one_place_relationships.py tests/integration/test_phase143_placement_adoption_matrix.py tests/integration/test_phase143_voice_resolution_adoption.py tests/integration/test_phase200_one_composition_root_processes.py tests/integration/test_phase200_working_context.py tests/integration/test_refinement_coordinator_kernel.py tests/unit/test_api_surface.py tests/unit/test_brief_mcp.py tests/unit/test_db_primitives.py tests/unit/test_design_system_guard.py tests/unit/test_desk_seed.py tests/unit/test_directory_name_uniqueness.py tests/unit/test_door_mcp.py tests/unit/test_door_read_model.py tests/unit/test_door_routes.py tests/unit/test_door_transport_parity.py tests/unit/test_event_linked_arm.py tests/unit/test_hs174_reach_wire.py tests/unit/test_kernel_effect_fence.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_mcp_phase133.py tests/unit/test_mcp_registration_characterization.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_mcp_thoughts.py tests/unit/test_mcp_tools.py tests/unit/test_notes_tag_query.py tests/unit/test_phase143_production_adoption.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase200_working_context_index.py tests/unit/test_phase200_working_context.py tests/unit/test_philo_architecture.py tests/unit/test_philo_census.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo5_compat.py tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_his_words.py tests/unit/test_philo5_loop_compat.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_pairs.py tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo5_the_loop_r2.py tests/unit/test_philo5_the_loop.py tests/unit/test_philo7_compat.py tests/unit/test_philo7_contract.py tests/unit/test_philo7_discovery.py tests/unit/test_philo7_rename_repair.py tests/unit/test_philo7_shelf_alignment.py tests/unit/test_primitive_contract.py tests/unit/test_project_mcp_palette.py tests/unit/test_refinement_context_service.py tests/unit/test_refinement_coordinator.py tests/unit/test_refinement_default_context.py tests/unit/test_refinement_thought_service.py tests/unit/test_residual_service_admission.py tests/unit/test_resourceful_service.py tests/unit/test_thought_workbench_backend.py tests/unit/test_thread_decide_always.py tests/unit/test_thread_family.py tests/unit/test_thread_people_fence.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_tool_loop.py tests/unit/test_voice_resolve.py tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync_primitives.py tests/unit/test_web_routes_thoughts.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 67e475a018d8f95af5560d1e7737f2a472bafc8c

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
........................................................................ [ 38%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 66%]
........................................................................ [ 72%]
........................................................................ [ 77%]
........................................................................ [ 83%]
........................................................................ [ 89%]
........................................................................ [ 94%]
.....................................................................    [100%]
1293 passed in 54.81s
```
