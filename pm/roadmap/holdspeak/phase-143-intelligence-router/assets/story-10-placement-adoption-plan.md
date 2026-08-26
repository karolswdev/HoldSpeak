# HS-143-10 — Placement Adoption Plan

**Status:** implementation plan  
**Story boundary:** adopt the existing server-owned assignment / frozen-plan /
controller / `InferenceRunner` spine for the non-tool callers listed in Story 10.
This is an adoption and retirement plan, not a second routing system and not a
route-editor design.  The public assignment glass remains Story 13 work.

## Non-negotiable implementation rules

1. `InferenceAssignment@1` remains sparse assignment truth and
   `InferenceRoutePlan@1` remains the immutable public route evidence.  At
   admission, private request material belongs in the operation plan; execution
   then uses the controller's reservation and `InferenceRunner`, never a fresh
   target lookup.  This is the contract's route-plan/operation-plan split
   (`assets/architecture-contract.md:228-296`) and controller waist
   (`assets/architecture-contract.md:364-403`).
2. A migrated legacy pointer is an **input to one atomic migration only**.  It
   must not remain a post-marker execution selector, shadow assignment data, or
   be dual-written indefinitely.  This follows the migration/deletion law
   (`assets/architecture-contract.md:503-524`).
3. The migration must create the assignment which produces the *same effective
   primary* as the old family on its first post-cutover admission.  It must not
   alter an exact-capability, group, or global assignment to accomplish that.
   The documented winner is one complete precedence chain, not concatenated
   tiers (`assets/architecture-contract.md:133-146`).
4. Every model attempt remains a consequential, separately admitted and
   receipted operation (Constitution Article XI, `docs/internal/CONSTITUTION.md:123-148`).
   A route change while a run exists can affect only a later parent admission;
   it cannot rewrite its frozen plan.  Hidden fallback is prohibited
   (Article VI, `docs/internal/CONSTITUTION.md:75-83`).
5. Do not treat the present `fallbackOnDevice` / `retryThenQueue` words as
   model-routing behavior.  The source census records that Python carry-through
   and surfaced-error behavior are not canonical fallback and that Swift retry
   execution has already been removed (`assets/generated-surface-fallback-census.md:54-56`).

## Obligation register

| ID | Acceptance / contract obligation | Required result | Owning slice | Production proof |
|---|---|---|---|---|
| O1 | Every caller uses the canonical resolver/controller and the `InferenceRunner` waist (story: `story-10-agents-workbenches-recipes-adoption.md:24-31`) | No migrated service resolves an execution target itself; each child has route-plan, operation-plan, controller execution, kernel admission, and runner receipt evidence. | 2–5 | Mutation and restart proofs cover Recipe, agent turn, Workbench, voice, Sequence, Workflow, legacy operation adapter, and every Swift leaf. |
| O2 | Preserve the old effective Workbench / Recipe / Agent primary until owner edit (story: `story-10-agents-workbenches-recipes-adoption.md:26-28`) | One-time per-family migration turns each nonblank legacy pointer into an exact subject/capability assignment without touching broader policy. Blank continues to inherit. | 1 | Seed legacy pointer + divergent global/group rows; compare the legacy result immediately before migration with first canonical frozen route after migration. |
| O3 | Subject edits apply next run only and do not rewrite group/global policy (story: `story-10-agents-workbenches-recipes-adoption.md:27-29`) | Editing/clearing a subject assignment changes a later admission only. Existing route/operation/execution evidence and group/global rows are byte-for-byte unchanged. | 1, 2–4 | Hold a parent after admission, mutate subject assignment, execute/restart parent, then admit a second parent and compare route legs and assignment rows. |
| O4 | `inference.run` cannot dispatch through mutable late resolution (story: `story-10-agents-workbenches-recipes-adoption.md:29-30`) | New calls cannot submit a mutable `requested_target_id` operation whose authorization resolves current placement. Old records remain readable but cannot become a physical dispatch path. | 4 | Submit a legacy-shaped record / mutate its target between request and authorize / prove refusal or frozen-adapter behavior and zero provider call. |
| O5 | Generated census converges to zero placement-resolution forks (story: `story-10-agents-workbenches-recipes-adoption.md:30-31`) | The AST/source census reports one canonical assignment resolver/controller path and zero family-local target resolution or late `inference.run` dispatch selectors. Fixtures are reduced because source was removed, not broadened to allow it. | 6 | Regenerated routing, capability, and surface-fallback census artifacts plus mutation tests. |
| O6 | No Apple physical leaf remains unadmitted; Swift retry/fallback prerequisite is verified first (story: `story-10-agents-workbenches-recipes-adoption.md:31-33`) | All seven currently censused Swift physical calls obtain a server-issued frozen attempt / reservation before transport. The two Story-06 runtime execution sites remain one-call-only. | 5 | Scanner sees zero unadmitted leaves; Swift tests prove a server reservation is consumed once and no local retry/alternate branch is revived. |
| O7 | Tool-bearing fallback remains Story 09's authority, while Story 10 names the first real adopter (Story 09 boundary: `assets/story-09-tool-foundation-plan.md:3-4`; foundation intentionally internal-only: `holdspeak/services/tool_turn_service.py:31-39`) | A single real agent-turn surface invokes the existing `ToolTurnFoundationService`; it does not recreate a loop, lease, palette, tool dispatch, or fallback policy. | 2 | Production-path test traverses application entry → foundation service → model-step controller → `InferenceRunner`; no direct engine completion occurs. |
| O8 | Egress / refusal / receipt truth is preserved (Constitution Articles III, V, VI, IX, XI: `docs/internal/CONSTITUTION.md:41-47`, `62-83`, `104-112`, `123-148`) | No fallback or Apple bridge hides a destination, changes frozen egress, or launders an unavailable/error result into success. | 2–5 | Assert frozen leg evidence, terminal receipt disposition, and zero child attempts in pre-dispatch refusal cases. |

## Current-tree inventory and disposition

The line references below identify the code or census record actually inventoried.
“Retire” means remove it as an execution authority; a historical reader or wire
compatibility decoder may remain where stated.  “Already done” is deliberately
narrow: it does **not** mean the physical call is already admitted.

### Agents and Recipes

| Item | Current evidence | Disposition | Adoption / retirement rule |
|---|---|---|---|
| `RecipeRecord`, the first-class persona record, stores `tools` and legacy `profile_id` | `holdspeak/db/models/knowledge.py:94-121` | **MIGRATE** (`profile_id`); **RETIRE** (`tools` as an execution authority) | Map a record's `profile_id` to that record's `recipe` subject assignment for `recipe.run` and `recipe.chat`. Do not activate arbitrary persisted tool names as a side effect of pointer migration. |
| `RecipeService.run` resolves `_target` then calls its direct runner helper | `holdspeak/services/recipe_service.py:68-84` | **MIGRATE** | Build/admit one route with capability `recipe.run`; render from the frozen operation material and execute only through `RoutedInferenceCoordinator` / fallback controller / runner. |
| `RecipeService.chat` repeats `_target`, then direct invocation | `holdspeak/services/recipe_service.py:85-124` | **MIGRATE** | Keep ordinary chat on `recipe.chat`; use the bounded agent-turn bridge described in Slice 2 when the caller is the elected ToolTurn surface. |
| Recipe `_target` reconstructs `invocation → workbench → recipe.profile_id` placement | `holdspeak/services/recipe_service.py:129-134` | **RETIRE** | Delete it after the migration adapter and canonical subject resolver own that precedence. No response code may independently re-resolve it. |
| Recipe `_payload` independently resolves placement for display | `holdspeak/services/recipe_service.py:171-174` | **RETIRE** | Project route summary/effective assignment from canonical evidence; never issue a display-only mutable resolve at run time. |
| Recipe semantic transports | `holdspeak/mcp/tools.py:651-655`; `holdspeak/web/routes/primitives/recipes.py:100,115` | **ALREADY-DONE** as transports | Keep them thin callers of the migrated service. They must not accept a target that bypasses canonical assignment admission. |
| Agent-turn engine dispatch calls a validated engine's `_chat_completion_text` directly | `holdspeak/plugins/intelligence.py:337-373` | **MIGRATE** | Replace the physical direct completion in the elected production path with the Story-09 foundation façade; its route capability is already `agent.tool_turn` (`holdspeak/services/tool_turn_service.py:27,72-184`). |

### Workbenches and schedules

| Item | Current evidence | Disposition | Adoption / retirement rule |
|---|---|---|---|
| `WorkbenchRecord` stores execution and resolver pointers | `holdspeak/db/models/workbench.py:112-146` | **MIGRATE** | Use `profile_id` once to seed a `workbench` subject assignment for `workbench.item`; use `resolver_profile_id` once to seed `voice.reference_resolve`. Do not erase a blank or invent a broader default. |
| `WorkbenchRunner._target` resolves workbench and recipe pointers itself; `_invoke` calls runner directly | `holdspeak/services/workbench_runner.py:29-43` | **RETIRE** | Replace both helpers with a frozen child-admission helper. A parent run may create item/memory children, but every child must carry the parent's frozen assignment/route evidence rather than re-resolve current pointers. |
| Workbench run resolves separately for an item and a memory child | `holdspeak/services/workbench_runner.py:142-290`, especially `212,247` | **MIGRATE** | Freeze each authorized child at its parent admission boundary. Preserve existing kernel parent/item causation while removing mutable per-child placement reads. |
| Scheduled work re-resolves terms and deployment revision at validation | `holdspeak/services/schedule_delegation.py:14-24,100-122` | **MIGRATE** | On schedule enable, admit/freeze the delegated route/deployment terms and store their evidence. Scheduled execution uses those terms; owner amendment creates a later schedule revision, not a covert retarget. |
| Conductor delegates to `WorkbenchRunner` | `holdspeak/workbench_conductor.py:455-463,521-524` | **ALREADY-DONE** after runner cutover | It stays orchestration-only; do not add another resolver or provider call here. |
| `retry_mint` re-resolves placement | `holdspeak/services/workbench_service.py:163-193` | **RETIRE** | Mint/retry from the prior run's frozen receipt/route evidence. If it starts new model work, it is a new canonical admission. |
| `resolve_voice` requires `resolver_profile_id`, resolves mutable target, closes over direct runner call, and invokes legacy retry loop | `holdspeak/services/workbench_service.py:366-437` | **MIGRATE / RETIRE** | Use `voice.reference_resolve`, freeze before its parent starts, and run the one controller-owned fallback execution. Delete closure-owned runner dispatch and local recovery authority. |
| Workbench serializer persists the two legacy selectors | `holdspeak/services/workbench_service.py:463-476` | **MIGRATE** | Until Story 13 replaces the visual editor, domain writes must translate legacy selector edits into canonical subject-assignment changes after marker; records are no longer execution selectors. |
| Workbench browser surfaces are census-classified placement UI/transports | `tests/unit/test_phase143_surface_fallback_census.py:75-103` | **OUT-OF-SCOPE** for shared editor design | Do not build a parallel assignment editor. Slice 3 supplies only compatibility write-through/fencing needed to prevent the existing field from silently diverging; Story 13 owns shared editable glass. |

### Sequences and workflows

| Item | Current evidence | Disposition | Adoption / retirement rule |
|---|---|---|---|
| Local sequence/workflow `_target` resolves invocation override plus recipe default and `_invoke` calls runner | `holdspeak/services/sequence_workflow_service.py:30-46` | **RETIRE** | Replace with canonical assignment lookup at parent admission and frozen per-model-node route/operation plans. |
| `run_sequence` resolves/invokes each step | `holdspeak/services/sequence_workflow_service.py:111-145`, especially `129,133` | **MIGRATE** | Use `sequence.step` and controller-owned attempt executions, preserving step causation and restart identity. |
| `run_workflow` resolves/invokes each model node and labels carry-through `fell_back` | `holdspeak/services/sequence_workflow_service.py:147-210`, especially `180-198` | **MIGRATE / RETIRE** | Use `workflow.node`; rename carry semantics and receipts truthfully. It must never claim model fallback when it merely carries input. |
| Failure-policy vocabulary and `fallbackOnDevice` carry-through | `holdspeak/services/support.py:198,228-241,500-531` | **RETIRE** fake labels | Migrate persisted aliases at the boundary to an explicit `carry` / `hold` / named error vocabulary. Reject or decode-only `retryThenQueue`; do not add retry semantics here. |
| Sequence / workflow MCP and web transport endpoints | `holdspeak/mcp/families/sequence.py:93,127`; `holdspeak/web/routes/primitives/chains.py:57`; `holdspeak/web/routes/primitives/workflows.py:56` | **ALREADY-DONE** as transports | Preserve request shape only where compatible; they call the migrated service and never resolve placement themselves. |

### Reference resolution and legacy kernel operation

| Item | Current evidence | Disposition | Adoption / retirement rule |
|---|---|---|---|
| Voice reference resolution is a censused runner entrance | `assets/generated-inference-capability-census.md:90-117`; implementation at `holdspeak/services/workbench_service.py:366-437` | **MIGRATE** | This is the `voice.reference_resolve` migration in Slice 3, including frozen summary evidence and controller-owned retry/fallback. |
| Service `RunLifecycle` submits top-level mutable `inference.run` with `requested_target_id` | `holdspeak/services/support.py:72-96` | **RETIRE** | Convert to a historical/read compatibility adapter or a canonical-admission façade. It may never initiate physical dispatch from that pointer. |
| Web primitive duplicate `RunLifecycle` submits the same mutable operation | `holdspeak/web/routes/primitives/_shared.py:87,142-176` | **RETIRE** | Eliminate the duplicate execution pathway and call the single canonical façade. |
| `InferenceRunCodec` accepts `requested_target_id` and authorizes by `resolve_inference_target` | `holdspeak/kernel/inference.py:20-25,86-134` | **RETIRE** as executable codec | Preserve decoding/display of completed historical records only if needed by `holdspeak/services/invocation_service.py`; no new admission may reach physical dispatch through this mutable authorization. |
| `InferenceRunner.invoke` is the existing physical Python waist | `holdspeak/kernel/inference_runner.py:62,145-182,196-400` | **ALREADY-DONE** | Do not duplicate provider admission. All migrated Python work terminates here with a controller reservation. |

### Apple, companion, and mesh physical leaves

| Item | Current evidence | Disposition | Adoption / retirement rule |
|---|---|---|---|
| Local Llama direct completion | `apple/Sources/InferenceLlama/LlamaProvider.swift:115-124` | **MIGRATE** | Receive a server-issued frozen attempt/reservation before the local transport call and return its receipt/disposition to the server bridge. |
| Endpoint `URLSession.data(for:)` completion | `apple/Sources/Providers/Inference/OpenAIEndpointProvider.swift:31-62` | **MIGRATE** | Same admitted-attempt bridge; the client cannot choose/retry a route after admission. |
| Structured output owns a local retry loop | `apple/Sources/Providers/Inference/StructuredOutput.swift:51-68` | **MIGRATE / RETIRE** local retry | One client transport attempt per server reservation. Malformed/output disposition returns to controller; only it elects correction/fallback. |
| Mesh worker calls provider directly | `apple/Sources/Providers/Desktop/MeshServeWorker.swift:84-126` | **MIGRATE** | Convert to an admitted mesh attempt with receipt reconciliation, not an independently selected mesh fallback. |
| Companion coder answer calls provider directly | `apple/Sources/RuntimeCore/Companion/CoderAnswer.swift:96-111` | **MIGRATE** | Convert to the same bridge and route capability evidence; preserve the companion result contract. |
| Workflow runtime has a single provider/mesh call and dormant retry/fallback constructor terms | `apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift:20-57,168-175,319-350` | **ALREADY-DONE** for Story-06 retry retirement; **MIGRATE** for admission | Keep exactly one call per server reservation; do not reactivate `maxRetries`, backoff, or fallback provider. |
| Blueprint interpreter holds/carries or performs exactly one completion | `apple/Sources/RuntimeCore/Workbench/BlueprintInterpreter.swift:306-335` | **ALREADY-DONE** for Story-06 retry retirement; **MIGRATE** for admission | Preserve `hold` / `carry` behavior while making the one completion an admitted attempt. |
| Seven-leaf scanner and zero Swift-policy fixture | `tests/unit/test_phase143_inference_capability_census.py:311-361`; `tests/unit/test_phase143_surface_fallback_census.py:112-115,153-171,224-244` | **MIGRATE** evidence | Do not delete scanner rows as a bookkeeping escape. Replace direct calls with a scanner-recognized admitted bridge and make the physical-leaf result reach zero by source change. |

## Ordered build slices

Every slice ends by running its focused command in a fresh shell, reading the
captured output, and only then moving to the next slice.  Commands isolate
`HOME` because assignments, kernel records, and migrations touch the database.
Use a retained failure directory only when a test needs inspection; do not run a
later status/commit action behind a command chain.

### Slice 1 — Canonical subject migration and post-marker compatibility

**Purpose.** Add one named, one-way migration family for legacy Recipe and
Workbench pointers; make canonical assignment the only source of future
execution truth while keeping nonvisual legacy controls behaviorally honest.

**Production files.**

- Modify `holdspeak/services/inference_adoption_service.py` to extend the
  existing marker-first, atomic migration pattern at `2442-2548` for
  Recipe/Workbench pointer families, and register the Story-10 capabilities in
  the production evidence/capability tuple at `42-74`.
- Modify `holdspeak/services/inference_assignment_service.py` only to add a
  narrowly typed migration helper if the existing atomic helper cannot express
  all subject/capability rows in one transaction.  Reuse `set_assignment`
  (`256-394`), `clear_assignment` (`425-565`), and `resolve_effective`
  (`567-585`); do not make a second resolver.
- Modify `holdspeak/services/recipe_service.py` and
  `holdspeak/services/workbench_service.py` so post-marker legacy-field writes
  invoke the canonical assignment mutation path (or refuse with an explicit
  migration error), rather than silently persisting an execution-dead pointer.
- Modify `holdspeak/db/models/knowledge.py` and
  `holdspeak/db/models/workbench.py` only if an existing record accessor needs
  a clearly named migration-input/read-only distinction.  No new routing
  columns should be added.

**Mapping.**  For every nonblank legacy `RecipeRecord.profile_id`, create exact
`recipe`-subject rows for `recipe.run` and `recipe.chat`; for every nonblank
`WorkbenchRecord.profile_id`, create a `workbench` subject row for
`workbench.item`; for every nonblank `resolver_profile_id`, create a
`workbench` subject row for `voice.reference_resolve`.  Use the durable record
ID as subject ID, not the old target/profile ID.  A blank creates no override
and retains inheritance.  The marker and source-record map must be in the same
transaction as assignment writes, be idempotent on restart, and record whether
a legacy value was actually read.

**Proof files.**

- Add `tests/unit/test_phase143_subject_pointer_migration.py`.
- Extend `tests/unit/test_phase143_production_adoption.py`.
- Adapt `tests/unit/test_recipe_precedence.py`,
  `tests/unit/test_recipe_runner_migration.py`, and
  `tests/unit/test_workbench_runner_migration.py`.
- Extend `tests/unit/test_phase143_inference_route_plans.py` for frozen
  next-run-only mutation evidence.

**Required proof cases.**  Cover blank inheritance; a divergent global/group
row; invocation > workbench > recipe precedence; missing/dangling migrated
subject; double startup; transaction rollback; legacy field edit after marker;
and mutation after a parent has frozen.  Assert exact pre/post effective
primary, unchanged group/global rows, and route/operation plan hashes for the
already admitted parent.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_subject_pointer_migration.py \
  tests/unit/test_phase143_production_adoption.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_recipe_precedence.py \
  tests/unit/test_recipe_runner_migration.py \
  tests/unit/test_workbench_runner_migration.py --tb=short
```

### Slice 2 — Recipe execution and the first production ToolTurn adopter

**Purpose.** Migrate Recipe execution to frozen route/controller execution and
turn exactly one real agent-turn surface into Story 09's first production
adopter.

**[ORCH-CALL 1 — execute this choice.]**  The first production ToolTurn adopter
is the **agent turn**, concretely the `PluginDispatch.chat` path at
`holdspeak/plugins/intelligence.py:337-373`, not a Workbench run, Recipe step,
or Workflow node.  It already represents an agent-turn boundary and the
foundation already declares `agent.tool_turn` (`holdspeak/services/tool_turn_service.py:27`).
Replace its direct `_chat_completion_text` dispatch with a product-facing,
server-owned façade over `ToolTurnFoundationService`; do not expose its private
ledger API directly to browser/MCP callers.  This gives the smallest real
surface: one incoming turn, one terminal answer/tool-turn receipt, and no
Workbench scheduling/memory or Workflow failure-policy coupling.  Do **not**
make `RecipeRecord.tools` executable merely to manufacture this first adopter.
A later explicit catalog/palette surface can opt a recipe into this agent turn
under the Story-09 qualification law.

**Production files.**

- Modify `holdspeak/services/recipe_service.py`: replace `_target`, direct
  `_invoke`, and display re-resolution with one canonical admission/execution
  adapter using `RoutedInferenceCoordinator.admit` / `execute` (`holdspeak/services/inference_adoption_service.py:806-877,1260-1435`).
- Add a small product façade in `holdspeak/services/agent_turn_service.py` that
  owns application validation and delegates to
  `ToolTurnFoundationService`; it owns neither tools, route selection, retry,
  nor provider calls.
- Modify `holdspeak/plugins/intelligence.py` to call that façade rather than a
  direct engine completion.
- Modify `holdspeak/services/tool_turn_service.py` only to expose a
  deliberately narrow production façade contract if the current foundation
  interface needs typed application input.  Keep its direct production-surface
  absence assertion replaced by a precise allowlist for this one façade import,
  not by a broad exemption.
- Modify `holdspeak/mcp/tools.py` and
  `holdspeak/web/routes/primitives/recipes.py` only if they need to pass a
  caller identity/correlation ID to the migrated service.  They remain
  transports, never route authorities.

**Proof files.**

- Add `tests/integration/test_phase143_agent_turn_adoption.py`.
- Extend `tests/unit/test_phase143_tool_turn_routing.py`,
  `tests/unit/test_phase143_tool_turn_model_steps.py`, and
  `tests/integration/test_phase143_tool_turn_boundaries.py`.
- Adapt `tests/unit/test_recipe_runner_migration.py` and
  `tests/unit/test_placement_provenance.py`.

**Required proof cases.**  An ordinary Recipe run/chat produces one frozen
route plan and controller execution; a changed recipe/workbench assignment
between admission and execution cannot retarget it; a second turn sees the
edit; an `agent.tool_turn` refusal dispatches zero model children; and a
production agent turn with a qualified tool candidate follows the real
foundation ledger and uses `InferenceRunner` rather than the engine method.
The test must assert the route/operation/lease/attempt/receipt objects, not a
mocked method-call sequence.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_recipe_runner_migration.py \
  tests/unit/test_placement_provenance.py \
  tests/unit/test_phase143_tool_turn_routing.py \
  tests/unit/test_phase143_tool_turn_model_steps.py \
  tests/integration/test_phase143_agent_turn_adoption.py \
  tests/integration/test_phase143_tool_turn_boundaries.py --tb=short
```

### Slice 3 — Workbench items, scheduled delegation, and voice resolution

**Purpose.** Cut the Workbench family over without weakening its parent/item
causation, schedule receipt, or voice-reference behavior.

**Production files.**

- Modify `holdspeak/services/workbench_runner.py` to remove `_target` /
  `_invoke` and admit each authorized item or memory model child through the
  canonical coordinator using frozen parent evidence.
- Modify `holdspeak/services/workbench_service.py` to derive retry minting from
  frozen run evidence and to replace the voice closure/retry loop with a
  `voice.reference_resolve` route/controller execution.
- Modify `holdspeak/services/schedule_delegation.py` so enablement freezes the
  delegated terms and later execution consumes them; owner change produces a
  new scheduled revision.
- Modify `holdspeak/workbench_conductor.py` only to thread immutable parent
  context/correlation through to the migrated runner.
- Keep the existing browser source files listed by the surface census unchanged
  except for minimal compatibility transport changes needed to make a legacy
  selector write update the canonical subject assignment.  No shared editor,
  selector layout, or new UI grammar belongs here.

**Proof files.**

- Extend `tests/unit/test_workbench_runner_migration.py`.
- Add `tests/integration/test_phase143_workbench_route_adoption.py` and
  `tests/integration/test_phase143_voice_resolution_adoption.py`.
- Add `tests/unit/test_phase143_scheduled_route_terms.py`.
- Extend `tests/unit/test_one_path_provenance.py` and
  `tests/unit/test_one_path_cardinality.py`.

**Required proof cases.**  A Workbench with a legacy execution pointer preserves
its first primary; a mid-run subject/global edit does not move item or memory
children; a later run does; retry-mint reads historical route evidence; a
schedule's enabled terms cannot drift at fire time; an explicit owner schedule
amendment yields a later frozen plan; and voice reference resolution obtains a
controller receipt for each real attempt/fallback leg.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_workbench_runner_migration.py \
  tests/unit/test_phase143_scheduled_route_terms.py \
  tests/unit/test_one_path_provenance.py \
  tests/unit/test_one_path_cardinality.py \
  tests/integration/test_phase143_workbench_route_adoption.py \
  tests/integration/test_phase143_voice_resolution_adoption.py --tb=short
```

### Slice 4 — Sequence/workflow adoption and `inference.run` retirement

**Purpose.** Move model nodes to frozen controller executions and close the
remaining mutable late-dispatch operation without altering unrelated workflow
branching.

**Production files.**

- Modify `holdspeak/services/sequence_workflow_service.py` to eliminate local
  `_target` / `_invoke`; admit each model step/node with `sequence.step` /
  `workflow.node`, preserve node identity, and report controller dispositions
  honestly.
- Modify `holdspeak/services/support.py` and
  `holdspeak/web/routes/primitives/_shared.py` to remove duplicate
  `RunLifecycle` execution submission.  Point both at one canonical admission
  façade or make them historical readers.
- Modify `holdspeak/kernel/inference.py` to reject new executable
  `inference.run@1` admission before mutable authorization; retain only a
  decode/read projection if old terminal records require it.  Do not replace
  `resolve_inference_target` with a different late resolver.
- Modify `holdspeak/services/support.py` failure-policy definitions and
  `holdspeak/services/sequence_workflow_service.py` receipt vocabulary:
  translate old wire aliases at input, then emit only truthful `carry`, `hold`,
  skip, or explicit failure semantics.  No `fell_back` receipt for carry.

**Proof files.**

- Extend `tests/unit/test_sequence_workflow_runner_migration.py`.
- Add `tests/unit/test_phase143_inference_run_retirement.py` and
  `tests/integration/test_phase143_sequence_workflow_restart.py`.
- Extend `tests/unit/test_phase143_inference_fallback_controller.py`,
  `tests/unit/test_one_path_spine.py`, and
  `tests/unit/test_phase143_surface_fallback_census.py`.

**Required proof cases.**  Mutating a node/recipe subject assignment after
workflow admission leaves its frozen route unchanged; crash/restart reconstructs
the same node attempt; a mutable legacy `requested_target_id` has zero physical
dispatches; historical terminal records remain viewable; `fallbackOnDevice`
compatibly decodes to carry without a fallback leg/receipt; and `retryThenQueue`
is a typed named refusal/legacy-only decode, never retry authority.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_sequence_workflow_runner_migration.py \
  tests/unit/test_phase143_inference_run_retirement.py \
  tests/unit/test_phase143_inference_fallback_controller.py \
  tests/unit/test_one_path_spine.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/integration/test_phase143_sequence_workflow_restart.py --tb=short
```

### Slice 5 — Apple/companion/mesh admitted-attempt bridge

**Purpose.** Remove the seven remaining unadmitted Swift physical leaves
without putting retry/fallback policy back into Swift.

**[ORCH-CALL 2 — execute this choice.]**  Use one versioned,
server-owned **admitted-attempt bridge**: the server freezes the route and
creates/reserves the attempt through `InferenceFallbackController`; the Apple
client receives only the minimum opaque attempt/transport material, performs
exactly one named transport call, and reconciles the classified outcome to that
attempt.  Add the bridge client at
`apple/Sources/RuntimeCore/Inference/AdmittedInferenceClient.swift` and its
server boundary at `holdspeak/services/apple_admitted_inference_service.py`.
This is a thin transport adapter over existing `RoutedInferenceCoordinator` /
`InferenceRunner` evidence, not a second resolver, local policy loop, or new
provider SDK.  The server refuses a bridge request absent a frozen route and
reservation; the client cannot select an alternate deployment.

**Production files.**

- Add `holdspeak/services/apple_admitted_inference_service.py`, composed from
  `RoutedInferenceCoordinator` and `InferenceFallbackController`; add the
  smallest authenticated application transport endpoint beside the existing
  inference application routes, rather than exposing raw database/ledger APIs.
- Add `apple/Sources/RuntimeCore/Inference/AdmittedInferenceClient.swift` and
  an accompanying typed receipt/disposition model in that same directory.
- Modify the seven leaves:
  `apple/Sources/InferenceLlama/LlamaProvider.swift`,
  `apple/Sources/Providers/Inference/OpenAIEndpointProvider.swift`,
  `apple/Sources/Providers/Inference/StructuredOutput.swift`,
  `apple/Sources/Providers/Desktop/MeshServeWorker.swift`,
  `apple/Sources/RuntimeCore/Companion/CoderAnswer.swift`,
  `apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift`, and
  `apple/Sources/RuntimeCore/Workbench/BlueprintInterpreter.swift`.
- Preserve the Story-06 one-call behavior in WorkflowRunner and
  BlueprintInterpreter.  In StructuredOutput, delete the local loop rather
  than wrapping each retry in a client-selected call.

**Proof files.**

- Add `tests/integration/test_phase143_apple_admitted_attempts.py` and extend
  `tests/unit/test_phase143_inference_capability_census.py` with explicit
  bridge-recognition/zero-direct-leaf assertions.
- Extend `apple/Tests/InferenceLlamaTests/LlamaProviderTests.swift`,
  `apple/Tests/ProvidersTests/EndpointProviderTests.swift`,
  `apple/Tests/ProvidersTests/MeshServeWorkerTests.swift`,
  `apple/Tests/ProvidersTests/StructuredOutputRobustnessTests.swift`,
  `apple/Tests/RuntimeCoreTests/CoderAnswerTests.swift`,
  `apple/Tests/RuntimeCoreTests/WorkflowRunnerTests.swift`, and
  `apple/Tests/RuntimeCoreTests/BlueprintInterpreterTests.swift`.

**Required proof cases.**  Assert: no bridge reservation means no transport;
one reservation means exactly one transport; malformed/disconnect/unavailable
outcomes reconcile to the same server attempt and only the server may select a
next leg; Stop/terminal outcomes never dispatch again; frozen egress/deployment
cannot change after server admission; and all Story-06 source tests still show
zero executable Swift retry/fallback branches.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/integration/test_phase143_apple_admitted_attempts.py --tb=short
```

Run the native complement separately after reading the Python output:

```bash
cd /Users/karol/dev/tools/HoldSpeak/apple && swift test \
  --filter 'LlamaProviderTests|EndpointProviderTests|MeshServeWorkerTests|StructuredOutputRobustnessTests|CoderAnswerTests|WorkflowRunnerTests|BlueprintInterpreterTests'
```

### Slice 6 — Honest census convergence and whole-object regression gate

**Purpose.** Make the generated evidence prove the source has converged, then
run end-to-end mutation/restart evidence across every migrated family.

**Production/evidence files.**

- Modify `tests/unit/test_phase143_routing_authority_census.py` only to encode
  the real post-cutover zero-fork invariant.  Its present exact resolver/pointer
  fixtures and AST scan are at `48-233,285-317`; do not weaken exact equality
  or the late-selector mutation test.
- Modify `tests/unit/test_phase143_inference_capability_census.py` only to
  represent the actual admitted bridge and eliminated direct leaves; preserve
  the model-site, runner-entrance, semantic-caller, and Swift scanner coverage
  (`54-361,534-653`).
- Modify `tests/unit/test_phase143_surface_fallback_census.py` only after the
  fake labels/local helpers are gone; preserve its source scanner and empty
  executable Swift-policy invariant (`25-115,118-244`).
- Regenerate and commit together the derived evidence files:
  `assets/generated-routing-authority-census.md`,
  `assets/generated-inference-capability-census.md`, and
  `assets/generated-surface-fallback-census.md`.

**Proof files.**

- Add `tests/integration/test_phase143_placement_adoption_matrix.py` covering
  Recipe, Workbench, agent turn, voice, sequence, workflow, legacy-operation
  refusal, and Apple bridge in one table-driven real-object matrix.
- Extend `tests/unit/test_one_path_census.py`,
  `tests/unit/test_one_dial.py`, and the three Phase-143 census modules above.

**Required proof cases.**  For every listed caller, prove (a) only the
canonical resolver selects terms, (b) assignment mutation after admission does
not change the old route, (c) a later admission observes it, (d) every actual
attempt has kernel/route/controller/runner receipt linkage, and (e) no family
reaches a provider through a local selector.  Regeneration must fail closed if
an uncatalogued resolver, runner entrance, or Swift physical leaf appears.

**Focused command.**

```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
  uv run --python 3.13.11 pytest -q \
  tests/unit/test_one_path_census.py \
  tests/unit/test_one_dial.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/integration/test_phase143_placement_adoption_matrix.py --tb=short
```

Then run the project full-suite command from `CLAUDE.md`, excluding metal as
specified there, before changing the story to done.  Capture that command
through `dw evidence capture`, read the output, and record any inherited
failures separately rather than calling a non-green suite a pass.

## Explicit non-decisions and boundaries

- **No new route editor in Story 10.**  The service compatibility layer may
  translate an existing selector write so it cannot silently diverge from
  assignment truth, but shared editable assignment UI is Story 13.  This
  honors Story 10's stated out-of-scope boundary (`story-10-agents-workbenches-recipes-adoption.md:17-22`) while meeting its note that shared UI ultimately replaces,
  rather than duplicates, private selectors (`:42-44`).
- **No ToolTurn reimplementation.**  The controller, lease, tool call ledger,
  qualified-route filter, and `ToolModelAdapter` are Story 09 authority.  Its
  model adapter deliberately renders/transports/parses one candidate with no
  loop/retry (`story-09-tool-turn-routing-safe-fallback.md:55-67`).
- **No new persistence family unless demonstrated necessary.** Existing
  assignment, migration-marker, route-plan, operation-plan, parent-bundle, and
  fallback execution structures already match the desired ownership.  If the
  admitted-attempt bridge proves a durable additive schema need, use the
  repository reconciliation path and update its schema snapshot/tests in the
  same slice; never add an untracked mutable selector column.
- **No cosmetic census pass.** Do not move a forbidden source site to an
  allowlist, rename an unadmitted provider call, or delete generated rows until
  the physical source is behind the admitted bridge.

## Risk register

| Risk | Failure mode | Guard / acceptance evidence | Owner slice |
|---|---|---|---|
| Legacy mapping changes precedence | Mapping uses old target ID as subject ID, or writes a broad assignment, so existing effective primary changes | Seed divergent invocation/workbench/recipe/group/global data and compare legacy vs first canonical frozen route; assert only exact subject rows changed | 1 |
| Dual-write divergence | Existing UI/API persists `profile_id` after marker while execution reads assignment | Route post-marker mutations through assignment or explicitly refuse; test legacy edit and inspect both record/assignment truth | 1, 3 |
| Frozen-plan bypass | A helper re-resolves before item/node/memory execution | Mutation-after-admission and restart tests assert route hash/leg evidence and source census finds no helper | 2–4, 6 |
| Tool foundation is only nominally adopted | Agent surface calls a façade that still directly invokes engine transport | Integration test asserts a real ToolTurn parent, lease, model-step execution, kernel child, and runner receipt; grep/census permits only the narrow façade import | 2 |
| Stored recipe tool names become ambient authority | Pointer migration accidentally turns inert `tools` into executable palette | First adopter has no recipe-field activation; only qualified server catalog manifests form a palette, per Story-09 route qualification | 2 |
| Schedule drift breaks owner intent | Fire-time validation resolves current deployment/assignment | Freeze at enablement; mutation requires a later schedule revision and old occurrence evidence remains stable | 3 |
| Fake fallback semantics reappear | `carry` gets emitted as `fell_back`, or Swift local retry returns under a renamed helper | Explicit receipt-vocabulary tests, source scan, and one-transport-per-reservation tests | 4–5 |
| `inference.run` history becomes unreadable | Removing executable codec also prevents display of old terminal records | Separate decoder/projection proof from new submission/authorization refusal proof | 4 |
| Apple bridge becomes a second policy center | Client chooses target, retries, or accepts unbound material | Server rejects missing/expired reservation; client has opaque one-attempt API; route/egress/receipt reconciliation tests | 5 |
| Census is gamed | Fixtures change without eliminating source fork | Exact equality plus mutation scanner; generated artifacts are reviewed against source diffs and fail on uncatalogued sites | 6 |
| Additive schema/reconcile break | A bridge ledger requires persistence and migrations damage an existing DB | Prefer current ledgers; if a new table is unavoidable, prove reconcile on an old-shape copy and update canonical snapshot tests | 5 |

## Orchestrator dispositions on the [ORCH-CALL]s (2026-08-25)

Both calls ACCEPTED as written, decided by the orchestrator as
tie-breaker (no counsel round — the design is ruled; these are
implementation granularity).

1. **First ToolTurn adopter = the agent turn** (`PluginDispatch.chat`,
   `holdspeak/plugins/intelligence.py:337-373`) behind a narrow
   product façade over `ToolTurnFoundationService`. The binding part
   of this disposition: `RecipeRecord.tools` stays INERT — no recipe
   field becomes executable palette authority in this story; only the
   Story-09 qualified-manifest law can ever form a palette. The
   foundation's direct-production-surface absence assertion is
   narrowed to a precise single-façade allowlist, never a broad
   exemption.
2. **Apple admitted-attempt bridge** as one versioned server-owned
   boundary (`apple_admitted_inference_service.py` +
   `AdmittedInferenceClient.swift`): no reservation → no transport;
   one reservation → exactly one transport; only the server elects a
   next leg. The client never gains a resolver, retry, or alternate
   deployment choice — the Story-06 retirement stays retired.

Build order: Slices 1+2 in one round, gate audit, Slices 3+4 in one
round, Slice 5, gate audit, Slice 6, full sweep, close. Terra workers
paired with opus-worker gate audits per the standing model law.

## Round-1 orchestrator triage and amended dispositions (2026-08-25)

Round 1 (Slices 1+2) verified by the orchestrator's own runs: Slice 1
focused set 67 passed; Slice 2 focused set 50 passed. The build worker
surfaced two design findings; ruled as follows.

1. **ORCH-CALL 1 AMENDED — the adopter anchor moves; the agent-turn
   election stands.** Inspection shows `PluginDispatch.chat` is NOT an
   unadmitted fork: the handle is minted by the host for one admitted
   child, identity-fenced to the runner-bound dispatch context
   (`holdspeak/plugins/intelligence.py:442-461,477-508`), and its
   completion is the last inch of an already-frozen reservation. The
   inventory row "Agent-turn engine dispatch … MIGRATE" is
   reclassified **ALREADY-DONE** (admitted leaf). Therefore the first
   production ToolTurn adopter is **`RecipeService.chat` on a
   tool-qualified frozen route**: at admission, when the route's
   qualified manifest is tool-qualified under the Story-09 law, the
   turn runs through `AgentTurnService.run()` →
   `ToolTurnFoundationService` (agent.tool_turn parent, lease/palette
   from the qualified manifest ONLY — `RecipeRecord.tools` stays
   inert); an unqualified route follows the Story-09 ruled fallback
   table. Recipes are the product's agent/persona primitive, so this
   is the genuine agent-turn surface, not a manufactured one. O7's
   proof becomes: transport entry → RecipeService.chat → façade →
   foundation → controller → InferenceRunner, production objects
   end-to-end. `AgentTurnService.dispatch_plugin` remains the single
   compatibility leaf for the admitted plugin handle.
2. **O2/workbench_id — worker's simplification ACCEPTED, ledgered.**
   No production transport passes `workbench_id` into standalone
   recipe run/chat (MCP allowed-list excludes it,
   `holdspeak/mcp/tools.py:649`; the web routes send none), so the old
   invocation→workbench→recipe tier was dead code on that entry and no
   tired-Tuesday effective primary changes. Workbench-context
   execution precedence is preserved where it is real — Slice 3's
   `workbench.item` migration. `workbench_id` on the recipe entry is
   context/attribution only. LEDGER NOTE, not a bug.

Round 2 = the ORCH-CALL-1 rewire (recipe.chat qualified-route
adoption) + Slice 3. Gate audit follows over Slices 1–3.

## OWNER RULING 2026-08-25 — Slice 5 DESCOPED

Mid-round-4 the owner ruled Swift/Apple work absolutely out of scope
for this story. The round-4 worker was stopped and its partial work
(the admitted-attempt bridge service/endpoint/client and all seven
Swift leaf edits) was discarded uncommitted; the three committed
rounds contain zero `apple/` changes. Consequences, binding on the
remaining slices:

1. **Slice 5 is struck.** ORCH-CALL 2's bridge design is recorded for
   whatever future phase gives Swift its recreation from the finished
   web spec; nothing of it ships here.
2. **Acceptance criterion 6 is descoped** (marked in the story file).
   Story 10's bar is the Python placement adoption: O1–O5, O7, O8.
3. **Slice 6's census convergence is Python-only.** The seven Swift
   physical leaves remain honestly censused as HELD leaves — the
   scanner rows stay, the zero-fork invariant applies to Python
   placement-resolution forks, and no fixture may claim a false Swift
   zero. Story 14 inherits this descope note for its kill-criteria
   ledger.

## Completion evidence checklist

Story 10 is ready to be marked done only when all six obligations O1–O6 have
production-object proof, the elected agent turn is demonstrably the first real
ToolTurn adopter (O7), both census families converge honestly, and the full
suite has been captured and read.  The final evidence should include the
pre/post effective-primary matrix, route/operation/execution identifiers and
receipts for every migrated family, the legacy `inference.run` no-dispatch
proof, Swift one-attempt bridge proof, and regenerated census artifacts.
