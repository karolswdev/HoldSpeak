I now have all the data needed. Let me assemble the final report.

---

# WAVE 1 SCOPING AUDIT

**Repository:** HoldSpeak, `main` @ `b4c6aced` (post-Phase 130/131/132/133).
**Scope:** Issue #450 Wave 1 -- "make ownership obvious."
**Method:** read-only; five parallel Opus forks + targeted reads; zero changes.

---

## 0. WHAT WAVES 0 AND PRIOR PHASES ALREADY DISCHARGED

Phase 130 (One Truth) shipped 11/11 stories closing Wave 0's execution-and-receipts lane:
- HS-130-01: `resolve_placement()` -- the ONE precedence authority (invocation > workbench > agent > global). `holdspeak/inference_targets.py:538-575`.
- HS-130-02: Injective secret slots. `holdspeak/intel/providers.py` `profile_key_env()`.
- HS-130-03: `DeploymentIdentity` -- one snapshot for readiness/execution/receipt. `holdspeak/inference_targets.py:96-117`.
- HS-130-05: `routing_profile` replaces `mir_profile`/`plugin_profile` as the canonical meeting routing field. One-time migration at `holdspeak/config/core.py:177-206`.
- HS-130-06: Ask no-retarget guard. `holdspeak/services/ask_service.py:137-139`.
- HS-130-07: Settings one-writer guard for web PUT. `web/src/pages/cores/__tests__/settingsWriters.test.ts`.
- HS-130-09: Workbench double-create and voice `set-agent` both fixed.

Phase 131 (One Admission Path) shipped 17/17 stories closing Wave 0's admission lane:
- Every model invocation now routes through `InferenceRunner.invoke()`.
- Immutable deployment revisions captured at admission.
- The one-path fence: `tests/unit/test_one_path_spine.py` (16 surfaces proven).

Phase 132 (The Working Desk) shipped 14/14 stories, bringing the full backend suite to 5703 passed / 0 failed.

Phase 133 (The Honest Sidecar) shipped 11/11 stories, expanding MCP from 52 to 82 tools with zero new side doors.

**Remaining from #450:** Wave 1 (ownership), Wave 2 (product language), Wave 3 (guards). This audit maps Wave 1.

---

## 1. THE DUAL API TODAY

### 1A. Server Routes (holdspeak/web/routes/primitives/profiles.py)

| Route | Method | Line | Handler | What it serves |
|---|---|---|---|---|
| `/api/profiles` | GET | :58-63 | `api_list_profiles` | Raw `ProfileRecord.to_dict()` array + mesh liveness |
| `/api/profiles` | POST | :76-78 | `api_create_profile` | **405** -- redirects to `/api/inference-targets` |
| `/api/profiles/{id}` | GET | :80-87 | `api_get_profile` | Raw `ProfileRecord.to_dict()` |
| `/api/profiles/{id}` | PUT | :89-91 | `api_update_profile` | **405** -- read-only |
| `/api/profiles/{id}` | DELETE | :93-95 | `api_delete_profile` | **405** -- read-only |
| `/api/inference-targets` | GET | :126-131 | `api_list_inference_targets` | `InferenceTarget.to_dict()` with readiness + `profile_alias` |
| `/api/inference-targets` | POST | :143-158 | `api_create_inference_target` | Write -- calls `ProfileService.create_profile` |
| `/api/inference-targets/{id}` | GET | :160-169 | `api_get_inference_target` | `InferenceTarget.to_dict()` |
| `/api/inference-targets/{id}` | PUT | :171-187 | `api_update_inference_target` | Write -- calls `ProfileService.update_profile` |
| `/api/inference-targets/{id}` | DELETE | :188-198 | `api_delete_inference_target` | Write -- calls `ProfileService.delete_profile` |
| `/api/inference-targets/{id}/probe` | POST | :133-141 | `api_probe_target` | Live reachability check |

The profile GET routes still serve raw `ProfileRecord` dicts. All writes go through `ProfileService` which stores to `db.profiles` and returns via `target_from_profile()`. The `_target_fields()` aliasing logic is duplicated: `profiles.py:100-124` AND `profile_service.py:139-167`.

### 1B. ProfileService (holdspeak/services/profile_service.py)

- `:75-86` `list_inference_targets()` -- imports from `inference_targets.py`, returns `TARGET_CONTRACT_VERSION` + `PROFILE_ALIAS_VERSION` + a `profile_alias` block advertising backward compatibility.
- `:139-167` `_target_fields()` -- the kind-aliasing map: `this_device` -> `onDevice`, `private_endpoint` -> `openAICompatible`, etc. Duplicated in the route file.
- `:169-171` `_target()` -- wraps any profile write's return through `target_from_profile()`.

### 1C. InferenceTarget contract (holdspeak/inference_targets.py)

- `:119-181` `InferenceTarget` dataclass -- the product contract. `to_dict()` includes a `profile_alias` block at `:175-179` that maps back to the profile id.
- `:340-475` `target_from_profile()` -- the adapter from `ProfileRecord` to `InferenceTarget`.
- `:478-481` `list_inference_targets()` -- `[this_machine_target()] + [target_from_profile(p) for p in db.profiles.list()]`.
- `:484-509` `resolve_inference_target()` -- resolves a target id, strips `profile:` prefix.

### 1D. MCP Tool Surface (12 of 82 tools touched)

**Profile CRUD family (5 tools, must rename):**

| Tool | Location | Risk |
|---|---|---|
| `profile.list` | `holdspeak/mcp/tools.py:231, :528-529` | HIGH -- returns profile-era shape |
| `profile.get` | `tools.py:232-236, :530-531` | HIGH |
| `profile.create` | `tools.py:238-243, :532-533` | MEDIUM -- already returns target contract |
| `profile.update` | `tools.py:244-252, :534-535` | MEDIUM |
| `profile.delete` | `tools.py:253-258, :536-539` | MEDIUM |

**Tools accepting `inference_target_id` (7 tools, param rename possible):**

| Tool | Location | Parameter |
|---|---|---|
| `ask.run` | `holdspeak/mcp/families/ask.py:46, :136-137` | `inference_target_id` |
| `ask.models` | `ask.py:12-19, :119-120` | returns destinations list |
| `recipe.run` | `tools.py:179, :485-488` | `inference_target_id` + `requested_placement` |
| `recipe.chat` | `tools.py:180, :489-492` | `inference_target_id` |
| `sequence.run` | `holdspeak/mcp/families/sequence.py:20, :99-100` | `inference_target_id` |
| `workflow.run` | `sequence.py:50, :133-134` | `inference_target_id` |
| `workbench.create/update` | `tools.py:171-172, :466-469` | `profile_id` in fields |

**Walk harness anchors:**
- `scripts/mcp_walk.py:184-220` -- asserts 82 tools by name (breaks on rename).
- `scripts/mcp_walk.py:365-407` -- live `.43` leg: calls `profile.create`, passes result as `inference_target_id` to `ask.run`.

**Test guards:**
- `tests/unit/test_mcp_tools.py:11-33` -- `REQUIRED_TOOLS` set.
- `tests/unit/test_mcp_phase133.py:123-127` -- asserts `REQUIRED_TOOLS` subset.

---

## 2. INHERITANCE POINTS

| Run kind | Resolver | File:Line | invocation | workbench | agent | global | Gap |
|---|---|---|---|---|---|---|---|
| Ask | `resolve_placement` | `ask_service.py:127` | YES | - | - | YES | No WB/Agent tiers |
| Recipe run | `resolve_inference_target` (NOT `resolve_placement`) | `recipe_service.py:130-131` | YES (manual) | - | YES (manual) | YES (manual) | **FULL GAP** -- bypasses precedence |
| Recipe chat | `resolve_inference_target` | `recipe_service.py:94` | YES (manual) | - | YES (manual) | YES (manual) | Same gap |
| Recipe listing | `resolve_placement` | `recipe_service.py:170` | - | - | YES | YES | Display only |
| Workbench runner | `resolve_placement` | `workbench_runner.py:30-31` | hardcoded None | YES | YES | YES | No invocation tier |
| Workbench service | `resolve_placement` | `workbench_service.py:340-341` | YES (resolver_profile_id) | - | - | YES | Different shape |
| Sequence/Workflow | `resolve_placement` | `sequence_workflow_service.py:31-33` | YES | - | YES | YES | No WB tier |
| Meeting intel | `resolve_meeting_placement` | `intel_plan.py:185-194` | YES (via intel_profile_id) | - | - | YES | Own parallel policy |
| Dictation | `resolve_placement` (conditional) | `speech_session/plan.py:611-624` | YES | - | - | YES | No WB/Agent; local bypass |
| Cadence | `resolve_placement` | `cadence_service.py:221` | - | - | - | YES | **No tiers at all** |
| Schedule delegation | `resolve_placement` | `schedule_delegation.py:18` | hardcoded None | YES | YES | YES | No invocation |
| Decision lifecycle | `resolve_placement` | `decision_lifecycle_service.py:71` | YES | - | - | YES | No WB/Agent |
| Rails observer | `resolve_placement` | `rails_observer.py:249-255` | YES | - | - | YES | No WB/Agent |
| Delivery PR | `resolve_placement` | `delivery_prs.py:234-241` | YES | - | - | YES | No WB/Agent |

**Key finding:** Recipe run/chat is the only execution path that does NOT use `resolve_placement`. It manually chains `inference_target_id or recipe.profile_id or "this_machine"` through `resolve_inference_target`. A Workbench override is invisible to Agent execution. The listing path at `recipe_service.py:170` DOES call `resolve_placement` correctly -- but only for display, not execution.

---

## 3. WRITERS -- "Only persistent writer" violations

### 3A. Discharged by Phase 130

- Readiness.tsx / useSpeakDeck.ts settings PUTs: CLOSED by HS-130-07. Guard: `web/src/pages/cores/__tests__/settingsWriters.test.ts:82-99`.
- CommandsCore.tsx: writes ONLY `dictation.macros.items` (not enablement). Guard: `settingsWriters.test.ts:61-71`.

### 3B. Still open (domain-object attributes, not settings)

| Preference | Writer | File:Line | Notes |
|---|---|---|---|
| `recipe.profile_id` | `RecipeService._recipe_fields` | `recipe_service.py:174` | Agent placement -- domain attribute, not a "setting" |
| `recipe.profile_id` | RecipeEditor | `RecipeEditor.tsx:118` | Canonical UI editor |
| `recipe.profile_id` | infoContract | `infoContract.ts:97` | **DUPLICATE:** Get Info writes the same field |
| `workbench.profile_id` | WorkbenchService | `workbench_service.py:432` | Workbench placement |
| `workbench.resolver_profile_id` | WorkbenchService | `workbench_service.py:433` | Workbench resolver |
| `skill.recipe_ids` | WorkbenchWindow | `WorkbenchWindow.tsx:1166-1190` | **Workbench mutates Agent-owned skill binding globally** |

### 3C. Issue #450's rulings on these

- "Agent Edit owns this decision. Get Info should summarize and hand off." (`infoContract.ts:97` is the violation.)
- "Agent Edit owns Agent skills. A Workbench may display inherited skills." (The `updateSkillBinding`/`attachSkill`/`detachSkill` at `WorkbenchWindow.tsx:1166-1190` is the violation.)
- Recipe and Workbench `profile_id` are legitimate domain attributes, not settings preferences. Wave 1 changes their semantics (nullable = inherit) but does not necessarily collapse them into Settings.

---

## 4. WEB OWNERSHIP

### 4A. Workbench Skill Binding

The Workbench renders skills as its own configuration and mutates the global `skill.recipe_ids`:

| Path | File:Line | What |
|---|---|---|
| `updateSkillBinding` | `WorkbenchWindow.tsx:1166-1175` | Calls `updateSkill(skillId, { recipe_ids })` globally |
| `attachSkill` | `WorkbenchWindow.tsx:1177-1181` | Appends recipe_id |
| `detachSkill` | `WorkbenchWindow.tsx:1183-1190` | Removes recipe_id |
| `approveSkill` | `WorkbenchWindow.tsx:1192-1197` | Sets `skill.status = "active"` |
| Skill display as Workbench's own | `WorkbenchWindow.tsx:231-249` | Filters by recipe_id |

### 4B. Get Info Placement Hand-Off

- `infoContract.ts:97` -- writes `profile_id` on the recipe.
- `InfoWindow.tsx:200-219` -- the UI that triggers it.
- Issue #450 says Get Info should summarize and link to RecipeEditor, not write.

### 4C. The Two Placement Dials (Phase 132 leftovers)

- `web/src/pages/cores/settingsModels.tsx:314` -- settings update path writes `["meeting", "intel_profile_id"]`.
- `web/src/pages/cores/SettingsCore.tsx:263` -- egress gate check reads `intel_profile_id`.
- Phase 132 shipped one meetings placement dial with visible provenance (HS-132-10), but the web still has the `intel_profile_id` key in settings models.

---

## 5. mir_profile / plugin_profile

### 5A. Declarations

| Field | Location | Status |
|---|---|---|
| `routing_profile: str = "balanced"` | `holdspeak/config/meeting.py:73` | CANONICAL (HS-130-05) |
| `mir_profile: str = "balanced"` | `meeting.py:77` | LEGACY -- kept for migration survival |
| `plugin_profile: str = "balanced"` | `meeting.py:90` | LEGACY -- kept for migration survival |

### 5B. The one accessor

`effective_routing_profile()` at `holdspeak/config/meeting.py:269-289` -- reads `routing_profile`, falls back to `mir_profile`, then `plugin_profile`, then default `"balanced"`.

### 5C. Runtime consumers

| Consumer | File:Line | What |
|---|---|---|
| `web_runtime.py` | `:183` | `self.mir_profile = normalize_profile(effective_routing_profile(...))` |
| `intel_queue.py` | `:149, :308` | `profile=effective_routing_profile(meeting_cfg)` |
| `commands/intel.py` | `:148, :150` | CLI display |
| `runtime/activity.py` | `:106` | Activity payload: `"profile": str(self.mir_profile)` |
| `runtime/routing_glue.py` | `:45, :323` | Runtime instance var |

### 5D. Migration writer

`holdspeak/config/core.py:177-206` -- `migrate_routing_profile()`: folds `mir_profile` (wins) or `plugin_profile` into `routing_profile` ONCE at load, resets both to `"balanced"`. Called at `core.py:298`.

### 5E. Validation

`meeting.py:171-174` -- `plugin_profile` validated as non-empty string. `meeting.py:176-179` -- `routing_profile` validated. Both legacy fields still participate in `__post_init__`.

**Status:** Phase 130 converged these at the accessor level. The legacy fields remain in the config schema and validation. Wave 1 would formally delete `mir_profile` and `plugin_profile` after the migration window.

---

## 6. SYNC

### 6A. What Phase 130/131 Fixed

The `SYNC_REGISTRY` at `holdspeak/services/sync_service.py:44` is the sole source of truth. `_BUCKET_KIND` is derived from it at `:52`. Workbenches are present in the registry, the merge map at `:75` includes `profile_id`, `resolver_profile_id`, `recipe_id`, `schedule`, `schedule_enabled`, `item_order`. Pull serializers exist at `:693-695`. Push merge at `:596-621` has special-cased bounded-delegation revocation.

### 6B. What Remains Broken for Wave 1

1. **Merge map field names** at `sync_service.py:75`: `recipe_id` becomes `capability_ref` (or whatever the general binding is renamed to). `profile_id` semantics change to "nullable override = inherit."
2. **Bounded delegation revocation** at `:596-621` is wired to `recipe_id` and `profile_id` changes -- these identity fields change shape under Wave 1.
3. **Sync's understanding of null `profile_id`**: today `null` means "no placement override set." Under Wave 1 inheritance, `null` means "inherit from agent." A device that syncs a workbench with `profile_id: null` must not interpret that as "use this_machine" on the receiving end. The merge map must distinguish "unset because inheriting" from "absent from the push payload."

---

## RISK REGISTER

### Risk 1: Recipe run/chat bypasses resolve_placement (CRITICAL)

**Seam:** `holdspeak/services/recipe_service.py:130-131` manually chains `inference_target_id or recipe.profile_id or "this_machine"` through `resolve_inference_target`, bypassing the 4-tier precedence. A Workbench override is invisible to Agent execution.

**Why naive migration breaks it:** Adding a workbench tier to Recipe without changing the execution path is a no-op; the listing shows correct provenance but execution ignores it.

**Guards:** `tests/unit/test_recipe_runner_migration.py` (recipe runner migration tests), `tests/unit/test_one_path_spine.py` (proves Recipe reaches InferenceRunner but does not test placement provenance), `tests/unit/test_placement_resolver.py` (tests the resolver itself but Recipe doesn't call it for execution).

### Risk 2: MCP profile.* tool rename breaks the 82-tool walk harness (HIGH)

**Seam:** `holdspeak/mcp/tools.py:231-258` (5 profile.* tools), `scripts/mcp_walk.py:184-220` (tool count assertion), `scripts/mcp_walk.py:365-407` (live `.43` leg calling `profile.create`), `tests/unit/test_mcp_tools.py:11-33` (REQUIRED_TOOLS set).

**Why naive migration breaks it:** Renaming `profile.*` to `destination.*` changes tool names, breaks the walk harness hardcoded tool references, changes the REQUIRED_TOOLS count, and may break any downstream MCP client that uses `profile.list`.

**Guards:** `tests/unit/test_mcp_tools.py`, `tests/unit/test_mcp_phase133.py`, `tests/unit/test_mcp_phase133_ask.py`.

### Risk 3: Sync merge-map field renames under live multi-device sync (HIGH)

**Seam:** `holdspeak/services/sync_service.py:75` (merge map), `:596-621` (bounded delegation revocation tied to `recipe_id` + `profile_id` changes).

**Why naive migration breaks it:** Renaming `profile_id` or changing its null semantics breaks the merge map's field-level conflict resolution. A device running old code pushes `profile_id`; a device running new code expects `target_override_id` or treats null as "inherit." Bounded delegation revocation at `:596-621` fires on `profile_id` changes -- if the field name changes, revocation silently stops.

**Guards:** `tests/unit/test_primitive_contract.py:194` (sync registry structural test), `tests/unit/test_sync_decision_records_127.py` (sync for decisions, not workbenches specifically), `tests/unit/test_workbench_runner_migration.py`.

### Risk 4: Get Info profile_id write competes with RecipeEditor (MEDIUM)

**Seam:** `web/src/desk/infoContract.ts:97` writes `recipe.profile_id`, duplicating `RecipeEditor.tsx:118`.

**Why naive migration breaks it:** If RecipeEditor is updated to the new inheritance vocabulary but infoContract is not, a Get Info edit can overwrite an inheritance-aware value with a raw profile_id, silently breaking the provenance chain.

**Guards:** No automated test currently guards against dual-editor writes to the same recipe field. The `settingsWriters.test.ts` fence covers Settings only, not domain object attributes.

### Risk 5: WorkbenchWindow skill mutation crosses the Agent boundary (MEDIUM)

**Seam:** `web/src/desk/components/WorkbenchWindow.tsx:1166-1190` mutates `skill.recipe_ids` globally via `updateSkill()`.

**Why naive migration breaks it:** If `recipe_id` becomes `capability_ref`, the skill binding mutation at `:1171-1172` reads/writes the wrong field. Additionally, if skills move to Agent-owned binding (per #450), removing the Workbench mutation path must not leave orphaned skill references or a UI that appears editable but silently fails.

**Guards:** `tests/unit/test_one_path_spine.py` (tests workbench execution, not skill binding). No specific test guards the skill-binding mutation path.

---

## PROPOSED SLICING: Wave 1 in 8 stories

### Story 1: Recipe execution takes the precedence door (KEYSTONE)

**What:** Migrate `recipe_service.py:130-131` (run) and `:94` (chat) from `resolve_inference_target` to `resolve_placement`, passing `invocation=`, `workbench=` (from caller context when available), and `agent=recipe.profile_id`. The listing path at `:170` already does this correctly -- align execution with it.

**Depends on:** nothing.
**Anchors:** `recipe_service.py:94,130-131,170`, `inference_targets.py:538-575`.
**Test coverage:** `test_recipe_runner_migration.py`, `test_one_path_spine.py`, `test_placement_resolver.py`.

### Story 2: One target spec replaces Profile + InferenceTarget dual API

**What:** Retire the `GET /api/profiles` read routes (return 301 to `/api/inference-targets`). Remove the duplicated `_target_fields()` from `profiles.py:100-124` (keep the one in `profile_service.py:139-167`). Remove `PROFILE_ALIAS_VERSION` and `profile_alias` blocks from `inference_targets.py:175-179` and `profile_service.py:81-86`. Wire `list_inference_targets` to return target spec + status directly (it already does via `target_from_profile`).

**Depends on:** nothing (parallel with Story 1).
**Anchors:** `profiles.py:58-95,100-131`, `profile_service.py:75-86,139-167`, `inference_targets.py:175-179`.
**Test coverage:** `test_web_routes_primitives.py`, `test_inference_targets.py`.

### Story 3: MCP profile.* tools become destination.* tools

**What:** Rename `profile.list/get/create/update/delete` to `destination.*` in `tools.py:231-258,528-539`. Update `REQUIRED_TOOLS` in `test_mcp_tools.py:11`. Update `scripts/mcp_walk.py:184-220,365-407`. Update param names in `ask.run/sequence.run/workflow.run` schemas if desired.

**Depends on:** Story 2 (the API behind the tools must be settled first).
**Anchors:** `tools.py:231-258,528-539`, `scripts/mcp_walk.py:184-220,365-407`, `test_mcp_tools.py:11-33`, `test_mcp_phase133.py:123-127`.

### Story 4: Effective target + provenance in API responses

**What:** Every placement-resolving API (Ask, Recipe, Workbench, Sequence, Workflow) returns `{ effective_target_id, source }` from `PlacementResolution.placement_dict()` (already defined at `inference_targets.py:525-530`). Recipe listing already does this; extend to execution responses. Add provenance to MCP tool responses where `inference_target_id` is accepted.

**Depends on:** Story 1 (Recipe must use resolve_placement for provenance to be meaningful).
**Anchors:** `inference_targets.py:525-530`, `ask_service.py:127`, `workbench_runner.py:30-31`, `sequence_workflow_service.py:31-33`, `cadence_service.py:221`.

### Story 5: Settings the only persistent preference writer

**What:** (a) Make `infoContract.ts:97` read-only for `profile_id` -- summarize and hand off to RecipeEditor. (b) Make retry/recovery placement transient (already discharged by HS-130-07; verify and close). (c) Add a test guard (extending `settingsWriters.test.ts` pattern) that `profile_id` on a recipe can only be written from RecipeEditor.

**Depends on:** nothing (parallel).
**Anchors:** `infoContract.ts:97`, `RecipeEditor.tsx:118`, `InfoWindow.tsx:200-219`, `settingsWriters.test.ts`.

### Story 6: Agent skill binding out of Workbench mutation

**What:** Remove `updateSkillBinding/attachSkill/detachSkill/approveSkill` from `WorkbenchWindow.tsx:1166-1197`. Workbench displays inherited skills (from its agent's `recipe_id -> skill.recipe_ids` binding) as read-only. Add a "Edit in Agent" hand-off link. If a true Workbench skill override is needed, add `workbench_skill_overrides` to the schema -- but #450 says display-only is sufficient.

**Depends on:** nothing (parallel).
**Anchors:** `WorkbenchWindow.tsx:1166-1197,231-249,1430`.

### Story 7: Workbench sync and deletion repair

**What:** (a) Update sync merge map at `sync_service.py:75` for field renames (`recipe_id` -> `capability_ref` if that ships in this wave, else deferred). (b) Verify null `profile_id` semantics under inheritance ("null = inherit" vs "null = unset"). (c) Verify bounded delegation revocation at `:596-621` fires correctly after field renames. (d) Add a sync round-trip test for workbench with nullable `profile_id`.

**Depends on:** Stories 1 and 2 (field names must be settled).
**Anchors:** `sync_service.py:44,52,75,596-621,693-695`, `test_primitive_contract.py:194`.

### Story 8: mir_profile / plugin_profile deletion and the walk

**What:** Remove `mir_profile` (`:77`) and `plugin_profile` (`:90`) from `MeetingConfig`. Remove their validation at `:171-174`. Simplify `effective_routing_profile()` at `:269-289` to read only `routing_profile`. Remove migration code at `config/core.py:177-206,298` (or keep it as a one-time no-op guard). Clean up runtime instance vars: `web_runtime.py:183` rename from `self.mir_profile` to `self.routing_profile`, propagate to `activity.py:106` and `routing_glue.py:45,323`. Walk the changes against the live hub.

**Depends on:** nothing (parallel, but should ship last as a cleanup).
**Anchors:** `meeting.py:73,77,90,171-179,253-256,269-289`, `config/core.py:177-206,298`, `web_runtime.py:183`, `activity.py:106`, `routing_glue.py:45,323`, `intel_queue.py:149,308`.
**Test coverage:** `test_intel_profile_resolution.py`, `test_one_dial.py`.

### Dependency graph

```
Story 1 (keystone) ─┬─> Story 4 (provenance in responses)
                    └─> Story 7 (sync repair)
Story 2 (unified API) ──> Story 3 (MCP rename)
Story 5 (one writer)     [parallel]
Story 6 (skill binding)  [parallel]
Story 8 (mir cleanup)    [parallel, ship last]
```

Minimum serial chain: Stories 1 -> 4 -> 7 is the critical path (3 stories). Stories 2 -> 3 is a second chain (2 stories). Stories 5, 6, 8 are independent leaves.