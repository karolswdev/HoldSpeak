# Close counsel -- Phase 156 The Front Door

**Verdict: RATIFY**

Zero must-fixes. Two should-fixes. Eleven recorded notes.

---

## SHOULD-FIX

> **Orchestrator, in-round (2026-08-31): both applied.** S1 — an
> all-legacy pack now FAILS the assignments step with a plain,
> actionable error ("open Advanced to add them to the library"), and a
> mixed pack's assignment receipt names its `unwired_legacy_groups`
> (front_door_service.py; tests
> `TestCounselS1LegacyOnlyPack`, 29/29 green). S2 — the strip's
> trailing " · change" removed; the Change action button stands alone
> (frontDoor.tsx; vitest 13/13 green).


### S1. Legacy GGUF groups skip assignment -- plan says "done" but the door loops

`front_door_service.py:1044-1047`: `_resolve_group_assignments` skips
items where `kind == "legacy_gguf"` with an explicit `continue`. When
ALL six LLM groups use a legacy GGUF as their source (the only path
when the desk has no reachable endpoint, no downloadable catalog
presets, and a legacy GGUF configured with llama.cpp), the list of
group_assignments is empty and the assignment step is a no-op.

- **Repro:** fresh desk with only a legacy GGUF model path in the
  TOML config and llama.cpp available. No LAN endpoints, no catalog
  presets. The recommender (`_pick_llm_for_group`, line 262-277)
  selects `kind="legacy_gguf"` for all six LLM groups. The user
  confirms a pack. `_run_plan` processes each item, marks it DONE
  (line 961-963, "Already present locally"), and collects zero
  group_assignments. The plan status is DONE. The client re-fetches
  `getAssignmentSummary()`, which reads the DB-backed assignment
  tables (not the legacy config). All groups show `no_assignment`.
  `hasUnconfiguredGroups` (frontDoor.tsx:123) returns true. The door
  renders the cards phase again.
- **Consequence:** the user sees: pick a pack, confirm, plan completes
  successfully, and the door immediately resets to the cards view.
  A loop. No data loss -- the legacy config still works independently
  of the assignment system -- but the UX is broken for this specific
  hardware shape.
- **Fix:** either (a) create a v2 profile from the legacy GGUF path
  and assign it via `set_assignment` in the apply engine, or (b) do
  not offer packs whose LLM groups are all legacy_gguf (they add
  nothing the desk does not already have), or (c) make the door's
  `hasUnconfiguredGroups` aware of the legacy config path.

### S2. Health strip text "change" is redundant with the "Change" button

`frontDoor.tsx:302-307`: the ok-tone ActionNotice renders
`Everything wired · Balanced · change` as its children text AND an
action button with label `"Change"` (line 301). The word "change"
appears twice in the rendered output: once in the message body and
once on the button.

- **Consequence:** minor wording noise. The settled design D3 says the
  strip is `"Everything wired · Balanced pack · change"` -- the
  design intends "change" as the clickable action, not separate
  text alongside it. The current rendering duplicates the word.
- **Fix:** remove `· change` from the children text. The button
  already provides the action affordance.

---

## RECORDED NOTES

### R1. The 11 RECORDED checklist items are correctly classified

`assets/concierge-ux-checklist-05.md`: the 11 RECORDED items are
backend/API gaps, not door-path surface defects. Items 2-5
(context_ceiling=0, FK errors, no-profile-on-download,
zero-candidates) are bugs in the existing services that the door
calls through. The context_ceiling=0 bug was patched by the reconcile
backfill at `reconcile.py:1120-1147` (idempotent UPDATE that copies
the correct value from inference_deployments). The others persist as
backend debt. None is a MUST-level gap mislabeled as out-of-scope:
they existed before Phase 156, the door does not introduce them, and
the door cannot fix them without owning those services.

### R2. Topology edge stroke visual weight

Story-06 shot sheet pass 2 notes: "the edge stroke deserves more
visual presence at 1440." Confirmed: `topology-surface.css` sets the
edge `stroke-width: 1.5`. At 1440 width with the SVG viewBox scaled
to the content bounds, the edges are thin. Not a gate blocker -- the
edges are visible and the bundled flow labels carry the semantic
weight. Polish for a future pass.

### R3. Deny-list fence coverage

`frontDoor.test.tsx:378-383`: the deny-list covers five terms
(`catalog`, `no_assignment`, `no_compatible_assignment`,
`provider_family`, `.gguf`). Internal terms like `preset`,
`boundary`, `runtime_id` are not on the list. This is sufficient
because the door surface renders `display_lines` from the recommender
(human-readable labels built by `_build_assignment_line`) and
`repairCopy` (which composes attention sentences from the assignment
summary's repair field). Raw internal identifiers never reach the
rendered text. The fence covers the five terms most likely to leak
through the assignment-summary data path.

### R4. No concurrent POST /apply guard

`front_door.py:161-308` (POST /apply): two simultaneous requests
could both pass `get_plan_by_pack` at `front_door_service.py:834`
before either creates a plan, producing two plans for the same
pack_id. Bounded: owner-only API (`PrincipalKind.OWNER` check at
line 157), single browser, single confirm button (`confirmPack` at
`frontDoor.tsx:204` fires once on click). No real-world path to
concurrent confirm.

### R5. warpdrv clean

`git grep -i warpdrv -- '*.py' '*.ts' '*.tsx' '*.css'` returns zero
hits in source files. The warpdrv grammar remains in the plan and
phase docs only. No AGPL-sourced code.

### R6. Topology route instantiates service directly

`front_door.py:427`: the topology route creates
`InferenceAssignmentService(db)` directly instead of using
`ctx.inference_assignment_service`. Functionally correct (the call is
`asvc.assignment_summary(principal)`, a read-only projection).
Stylistically inconsistent with the recommendation and apply routes
which use context services. No correctness impact.

### R7. Visual gate shot sheets complete

Shot sheets exist for all four UI stories with 1440+393 shots and
verdicts:
- Story 03 (library patterns): PASS -- `assets/story-03-shot-sheet/index.md`.
- Story 04 (door surface): PASS on structure, three wording defects
  bound to story 05 -- `assets/story-04-shots/index.md`.
- Story 05 (plain words): PASS, all three bound defects visibly
  resolved -- `assets/story-05-shots/index.md`.
- Story 06 (topology): PASS (pass 2, after first FAIL for invisible
  flows and Add-node collision) -- `assets/story-06-shots/index.md`.
  The phase close requires the owner's eyes.

### R8. Fence baseline zero growth

`web/fence-baseline.json` was created in commit `11b65cf2` (HS-156-03)
and never modified afterward (`git log --oneline --follow e88a6065..7328757d -- web/fence-baseline.json` returns one commit). 61
private-imports, 0 library-css-outside, 6 roving-reimpl entries.
Zero growth across the phase's six subsequent commits.

### R9. Popover fix (9fcc7dd1) is sound

The Popover portals into `#desk-next` instead of `document.body` with
a body fallback. This matches the existing DeskMenu and DeskToolShelf
patterns. The commit message explains the root cause: the body-portal
escaped the `.desk-next` ancestor, so the content's scoped z-index
never applied while the unscoped backdrop's did, blocking pointer
events over the content. Four regression tests
(`patterns.test.tsx:+71 lines`) cover portal target, click-through
above backdrop, backdrop dismiss, and co-located container. 62 pattern
tests green.

### R10. Gallery private imports outside the fence scope

`ComponentsCore.tsx:1-57` imports directly from `surface/SurfaceFooter`,
`surface/gadgets`, `surface/Surface`, `surface/wings`, `surface/patterns`,
and `surface/graph/TopologySurface`. These are private imports but
ComponentsCore is the gallery page (`/design/components`) under
`src/pages/cores/`. The guard-architecture.mjs fence checks only
`src/desk/` files (lines 87-88: `if (!name.startsWith("src/desk/"))
continue`), so pages are outside the fence scope. All new phase code
(frontDoor.tsx, TopologyMapView.tsx, topologyService.ts) correctly
imports through the barrel (`from "../../desk/surface"`).

### R11. Inherited from 153-154

R1 multi-tool sibling gap, R2 paraphrase laundering, R4 bargedTurns
set cleanup (fixed in 154 S4). No change in Phase 156.

---

## Evidence reviewed

| Question | Verdict | Key evidence |
|---|---|---|
| Idempotency: define-endpoint on crash/re-apply? | **CLEAN.** `_ensure_profile` at `model_library_service.py:347-362` checks `_profile_matches` before the revision check. If the profile body matches the existing profile (same label, provider_family, model), it returns the current profile without raising a conflict. All six LLM groups sharing one endpoint produce the same `profile_id` and the same body, so calls 2-6 short-circuit via `_profile_matches`. Crash recovery: a RUNNING item falls through to re-execution, and `_ensure_profile` handles the existing profile. | `model_library_service.py:347-362`, `front_door_service.py:660-682,897-938` |
| No parallel authority (fence)? | **CLEAN.** `test_front_door_apply.py:581-670`: two structural tests scan the apply engine source for direct DB writes to library/assignment tables. The apply engine uses only `model_library_service.define_endpoint`, `model_library_service.download`, and `assignment_service.set_assignment`. Its own persistence goes through `db.front_door.create_plan` / `update_plan` writing to `front_door_apply_plans` (its own table). | `front_door_service.py:612-1082`, `test_front_door_apply.py:581-670` |
| Receipts on every step? | **CLEAN.** `test_front_door_apply.py:384-400`: the `test_receipts_for_every_step` test asserts that every item in a completed plan has `status == ITEM_DONE` and `receipt is not None`. Speech/TTS builtin items get synthetic receipts at `front_door_service.py:912-914,961-963`. | `front_door_service.py:912-914,926-928,950-951,982-984`, `test_front_door_apply.py:384-400` |
| Half-applied pack strands the desk? | **PARTIALLY.** A fault during provisioning sets the item to FAILED and the plan to FAILED immediately (`front_door_service.py:934-938`). The plan is persisted in the DB before returning. Resume re-applies from the first unfinished item (lines 860-877). The client shows the ProgressPlan with a "Resume" action button (`frontDoor.tsx:277-280`). Stranding via legacy GGUF: see S1. | `front_door_service.py:860-993`, `frontDoor.tsx:265-283` |
| Completeness law: hardware class with no viable speech? | **CLEAN.** `_build_pack` at `front_door_service.py:560-609` iterates all seven ASSIGNMENT_GROUPS. If `_pick_llm_for_group` returns None for any group, `return None` at line 584 drops the pack entirely (it is not offered). Speech recognition is always covered by `_speech_line` (line 592), which uses `_WHISPER_MODELS` with a hardcoded fallback to "base" (line 403). TTS is always covered by `_tts_line` (line 598). A pack that cannot be completed is never offered. | `front_door_service.py:560-609,396-436` |
| Probe boundary: nothing beyond known endpoints? | **CLEAN.** `_endpoint_facts` at `front_door_service.py:126-150` iterates only `known_endpoints` and probes each via `_default_probe` (or an injected test probe). `_default_probe` makes a single GET to `{base_url}/v1/models` with a 3-second timeout. No network-wide scan, no DNS discovery, no broadcast. The route at `front_door.py:88-99` populates `known_endpoints` from `db.profiles.list()` (existing profiles with `base_url`). | `front_door_service.py:91-150`, `front_door.py:88-99` |
| Credential-gated cloud? | **CLEAN.** `_pick_llm_for_group` at `front_door_service.py:225-326` does not have a cloud-credential path. Cloud endpoints are never offered because `has_cloud_credential` is passed but never consumed in the priority chain (endpoints, legacy_gguf, catalog are the only paths). The parameter exists for future use. The recommender never offers a cloud pack without an existing credential. | `front_door_service.py:225-326` |
| Pack determinism? | **CLEAN.** `recommend()` at `front_door_service.py:439-524` is a pure function over its inputs. The `_sha()` hash function (line 107-109) is used for replay detection, not for pack selection. The pack structure is deterministic for the same hardware + catalog + endpoints + legacy inputs. No random element, no time dependency, no external state. | `front_door_service.py:439-524` |
| Unconfigured-detection correctness (cards vs strip)? | **CLEAN.** `hasUnconfiguredGroups` at `frontDoor.tsx:122-126` filters to non-global rows and checks if ANY row lacks an `assignment`. `firstAttentionRow` (line 128-131) finds the first row with a non-null `repair`. The `phase` derivation (lines 181-190) checks: (1) active plan takes precedence, (2) unconfigured groups show cards, (3) everything else shows strip. Edge case: see S1 for the legacy GGUF loop. | `frontDoor.tsx:122-131,181-190` |
| ONE-action law on the surface? | **CLEAN.** The attention strip has exactly one ActionNotice with one action button (lines 293-304). The ok strip has exactly one "Change" action (lines 301-310, but see S2 for the text redundancy). The test at `frontDoor.test.tsx:300-310` asserts exactly one button with class `surface-action-notice-btn` and text "Fix it". | `frontDoor.tsx:293-316`, `frontDoor.test.tsx:296-310` |
| Advanced layer unreduced? | **CLEAN.** The advanced fold (`Disclosure` at frontDoor.tsx:318-340) renders `ModelLibraryCore` and `CapabilityAssignmentsCore` unchanged, wrapped in a view toggle (Map/Table at lines 324-326). The Map view is the topology; the Table view is the existing Library + Assignments. No features removed. | `frontDoor.tsx:316-344` |
| Every gesture writes through existing authorities? | **CLEAN.** Enumerated calls: (1) Add node / define-endpoint: `defineEndpoint` at `modelLibrary.ts` calls `POST /api/inference/model-library/define-endpoint`. (2) Add node / connect-hosted: `connectHostedModel` calls `POST /api/inference/model-library/connect-hosted-model`. (3) Re-point: `saveAssignment` calls `POST /api/inference/assignments/set`. (4) Inspector: `getAssignmentEditor` calls `GET /api/inference/assignments/editor`. (5) Apply: `POST /api/front-door/apply` calls `model_library_service.define_endpoint`, `model_library_service.download`, `assignment_service.set_assignment`. No new write authority. The mock in `topologyMap.test.tsx:31-51` rejects unknown URLs, providing structural coverage. | `TopologyMapView.tsx:348-419`, `topologyMap.test.tsx:31-51`, `front_door_service.py:653-776` |
| Fence baseline zero growth? | **CLEAN.** See R8. Created once, never modified. | `git log --follow -- web/fence-baseline.json` |
| Keyboard paths? | **CLEAN.** TopologySurface: Arrow keys navigate between nodes (nearestInDirection, line 134-159), Shift+Arrow pans (line 234-251), Home jumps to home node (line 280-288), Tab enters (roving tabindex, node tabIndex at line 386), Enter/Space on nodes (they are `<button>` elements). Popover: Escape dismisses (line 59-62), Tab trapped (line 64-80). ChoiceCardGroup: real `input[type=radio]` with proper grouping. RepointPanel: real `input[type=radio]` with `radiogroup` role. | `TopologySurface.tsx:134-288,386`, `Popover.tsx:55-80`, `ChoiceCardGroup.tsx`, `TopologyMapView.tsx:269-291` |
| Popover fix (9fcc7dd1) sound? | **CLEAN.** See R9. | `Popover.tsx:116-118`, `patterns.test.tsx:+71 lines` |
| Egress/custody: downloads badged and receipted? | **CLEAN.** The apply engine's download path calls `model_library_service.download` (front_door_service.py:697-698), which goes through the existing egress-badged download flow (model_library_service.download is the Phase 143+ download seam). The topology add-node hosted flow shows `EgressChip` (TopologyMapView.tsx:399). The define-endpoint flow does NOT show an EgressChip because a LAN endpoint is local (same_device/private_network boundary). Constitution Art. III satisfied. | `front_door_service.py:685-703`, `TopologyMapView.tsx:399` |
| Topology aggregator leaks nothing new? | **CLEAN.** The topology GET route (front_door.py:348-465) aggregates from `list_inference_targets`, `inspect_hardware`, `inspect_runtimes`, and `assignment_summary` -- all existing read-only projections. The response includes `base_url` for endpoint nodes (already visible in the Model Library) and model names (already visible). Owner-only access (PrincipalKind.OWNER check at line 354). No secrets, no keys, no credentials in the wire. Art. III: no new egress. | `front_door.py:348-465` |
| Cross-phase: front_door_apply_plans safe on long-lived DBs? | **CLEAN.** Schema at `schema.py:3545-3552` uses `CREATE TABLE IF NOT EXISTS` -- safe for existing DBs. No positional INSERTs: the DB repo at `front_door.py:34-38` names all columns explicitly: `(id, pack_id, status, items_json, created_at, updated_at)`. The reconcile path runs the full SCHEMA_SQL which includes all `CREATE TABLE IF NOT EXISTS` statements, so the table is created on schema reconcile. No ALTER needed (it is a new table, not a new column on an existing one). | `schema.py:3545-3552`, `front_door.py:28-38`, `reconcile.py` (implicit via SCHEMA_SQL execution) |
| Cross-phase: context_ceiling backfill interactions? | **CLEAN.** The backfill at `reconcile.py:1120-1147` runs idempotently: UPDATE ... SET context_ceiling = (SELECT ... WHERE > 0) WHERE context_ceiling = 0 AND EXISTS (...). Already-healed rows (context_ceiling != 0) are untouched. The define-endpoint path that created the 0-value rows (DeploymentRevision.from_identity) still runs for new profiles, but the backfill cures them on next reconcile. | `reconcile.py:1120-1147` |
| No modals, no prose, no window hooks? | **CLEAN.** No modal in any new component. The add-node form is an in-flow Disclosure (TopologyMapView.tsx:365-431), the re-point panel is inline (TopologyMapView.tsx:244-303), the pack cards are a radio group (ChoiceCardGroup). No `window.__hs`, no `(window as any)`, no `document.querySelector` in non-test code. | grep across new files |
| Tokens (no hard-coded colors)? | **CLEAN.** `frontDoor.css`, `topologyMap.css`, `topology-surface.css`, `choice-card.css`, `progress-plan.css`, `state-chip.css`, `action-notice.css`, `disclosure.css`, `popover.css`, `provenance.css` -- all use `var(--token, fallback)` pattern. Spot-checked: no bare hex without a token variable. | CSS files |
| 393 overflow? | **CLEAN.** Shot sheets at 393px exist for all UI stories. The topology map pans inside its container (`surface-topology` has `overflow: hidden` at `topology-surface.css:4`). The front door cards stack vertically. No horizontal page overflow. | shot sheets, `topology-surface.css:4` |
| Reconcile: front_door_apply_plans on existing DB? | **CLEAN.** See cross-phase entry above. `CREATE TABLE IF NOT EXISTS` is the guard. | `schema.py:3545-3552` |

---

## What the phase got right

Six stories delivering the front-door concierge UX: a pure recommender
that turns hardware facts + known endpoints into complete pack
recommendations, a durable and resumable apply engine that drives only
existing service seams (no parallel writer), a door surface that
replaces the raw Settings/Models page with three pack cards or a
one-line health strip, a jargon purge tested by a deny-list fence, a
component-library reform with a ratchet fence and visual gates, and a
topology map where every gesture is a real operation through existing
authorities.

The library reform (story 03) is the structural win: the surface
barrel, the contract, the seven v1 delight patterns, and the ratchet
fence landed as a prerequisite. The door and topology build FROM these
patterns (ChoiceCardGroup, ProgressPlan, ActionNotice, Disclosure,
StateChip, TopologySurface, Popover, ProvenanceChip) -- zero one-off
furniture. The fence baseline was written once and never grew across
the phase's six subsequent commits.

The apply engine proves its no-parallel-authority claim by structural
test: the source is scanned for direct DB writes to library/assignment
tables (test_front_door_apply.py:581-670), finding zero violations.
The define-endpoint idempotency holds because
`model_library_service._ensure_profile` matches the existing profile
body before checking the revision (model_library_service.py:348-354).
The plan persists after every step, and resume retries from the first
unfinished item.

The two should-fixes are bounded: S1 (legacy GGUF assignment loop)
affects only the rare hardware shape where a legacy GGUF is the sole
LLM source. S2 (strip text redundancy) is a one-line wording fix.

The visual gate process held: four shot sheets, five verdicts (story
06 failed pass 1 and was reworked before pass 2), the owner sees this
sheet in the phase exhibit.
