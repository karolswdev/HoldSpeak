# Intelligence Router architecture

The intelligence router turns a declared product capability into one receipted
physical model attempt. It keeps configuration useful without letting a later
configuration edit rewrite work that has already been admitted.

`capability registry -> model authority -> assignment -> frozen route -> frozen operation request -> controller -> InferenceRunner -> receipt`

Model Library makes models available. Assignments choose a compatible ordered
chain. The router freezes and executes one immutable attempt at a time. The
Library and Assignments are owner surfaces. The remaining stages are runtime
authority, not a model picker or an alternate provider API.

## 1. Scope, nouns, and ownership

A **capability** is a registered, revisioned description of one kind of
intelligence work. A **profile** is an immutable public model intent revision.
A **binding** connects that profile revision to an exact deployment revision,
including its enabled and readiness facts. A **deployment revision** is the
private execution identity that an adapter can use at dispatch. An
**assignment** is a sparse, local configuration row holding an ordered chain of
profiles. A **route plan** freezes the resolved assignment, capability,
deployment legs, policy, deadline, and preflight facts. An **operation request
plan** binds private serialized request material and budget evidence to that
route. An **execution** is the controller state machine over that frozen pair.
An **attempt** is one physical child. A **receipt** is its durable outcome, or
the controller's durable election over the route.

The definitions live in
[`holdspeak/inference_capabilities.py`](../../holdspeak/inference_capabilities.py),
[`holdspeak/services/model_profile_service.py`](../../holdspeak/services/model_profile_service.py),
and
[`holdspeak/services/inference_route_plan_service.py`](../../holdspeak/services/inference_route_plan_service.py).
Configuration is local authority. It is never a mutable instruction for an
already admitted execution. The distinction is deliberate: an owner needs to
be able to improve a Library row or an Assignment while work is running, yet an
in-flight provider attempt must retain the exact authority, material, and
boundary that were reviewed at admission.

## 2. Capability registry before model resolution

[`InferenceCapabilityRegistry`](../../holdspeak/inference_capabilities.py)
is a sealed process registry. Its immutable capability definitions carry exact
revisions, schemas and SHA-256 hashes, operation contracts, requirements,
allowed boundaries, and permitted retry policies. The registry composes built-in
capabilities, installed meeting-plugin revisions, and only bounded plugin
capability definitions. Its owner projection exposes compatible facts without
execution locators.

An adopter calls `require()` before it can resolve profiles. An unknown or
non-assignable capability therefore refuses before model selection. The
registry's retry policies are revisioned and hashed too, so a frozen route
records the policy whose fallback law it uses. The owner can inspect registered
jobs through
[`InferenceCapabilityApplicationService`](../../holdspeak/services/inference_capability_service.py)
and the `holdspeak://inference/capabilities` MCP resource implemented in
[`holdspeak/mcp/resources.py`](../../holdspeak/mcp/resources.py). Those are
registry projections, not a routing control.

## 3. Model authority and availability are separate

[`ModelProfileService`](../../holdspeak/services/model_profile_service.py)
creates immutable public profile revisions and binds one revision to an exact
deployment head and deployment revision. A binding records a readiness
observation for that exact deployment. Endpoint and key material do not become
profile fields. The private custody boundary is
[`ProfileKeyService`](../../holdspeak/services/profile_key_service.py).

[`ModelLibraryApplicationService`](../../holdspeak/services/model_library_service.py)
answers a different question: which models can be acquired, added, connected,
or checked. Every Library command snapshots assignment heads on both sides and
refuses if it changed them. Adding a file, downloading a catalog model, or
connecting a provider makes availability available. It does not route work.
Assignments are the only owner write authority that chooses a chain. This
separation also keeps a readiness observation honest. A Library row can be
present while its binding is disabled, unavailable, or not ready. Conversely,
an assignment can preserve a compatible chain while no member is currently
executable. Availability and selection are separate facts so the owner can
repair either without silently changing the other.

## 4. Sparse assignments and whole-chain precedence

[`InferenceAssignmentService`](../../holdspeak/services/inference_assignment_service.py)
stores one to four unique profile entries per assignment. It validates a whole
ordered chain, its enabled bindings, allowed capabilities, retry policy, and
compatibility. It does not merge lists or silently trim an invalid chain.

Resolution reads the first available whole assignment in this order:

1. invocation for the capability;
2. subject for the capability;
3. capability;
4. capability group;
5. global.

A subject is one of `thought`, `workbench`, `agent`, `recipe`, or `project`, and
its assignment is always capability-specific. A subject row is not a general
model pointer. Clearing a row with **Use default** exposes the next complete
chain in that order. It does not splice the cleared list into an inherited one.
The resolver records both the assignment revision and the source tier in the
route plan.

## 5. Freeze: route plan then operation request plan

`resolve_route_plan()` is read-only. It reads one SQLite snapshot, resolves the
assignment and deployment revisions, and performs no probe, model load, scan,
network work, or persistence. `freeze_route_plan()` persists that resolution
atomically. The frozen route contains the capability revision and hash,
assignment source and hash, ordered deployment revisions, retry policy,
deadline, and preflight eligibility. See
[`InferenceRoutePlanService`](../../holdspeak/services/inference_route_plan_service.py).

A route alone has no prompt bytes. The production evidence owner in
[`inference_adoption_service.py`](../../holdspeak/services/inference_adoption_service.py)
serializes the operation payload, records its hash and budget material, and
freezes one operation request plan bound to that route. Reconstruction verifies
stored hashes and uses the frozen pair. It never rereads assignment, profile,
binding, readiness, or configuration heads.

<a id="recipe-run-from-assignment-to-receipt"></a>
## 6. Recipe run from assignment to receipt

`RecipeService.run()` is a representative production path. Its `recipe.run`
capability and `recipe` subject make the assignment lookup explicit. If an
owner edits the selected assignment after admission, that edit can affect only
a later run: this run has already frozen its route and operation evidence.

| Step | Confirmed runtime owner | What happens |
|---|---|---|
| 1 | [`RecipeService.run()`](../../holdspeak/services/recipe_service.py) | Renders saved Recipe input, migrates and fences retired selectors, then admits `recipe.run` with `subject_kind="recipe"` and the Recipe id. |
| 2 | [`RoutedInferenceCoordinator.admit()`](../../holdspeak/services/inference_adoption_service.py) | Requires `recipe.run`, stages canonical production material, and opens one immediate transaction. |
| 3 | [`InferenceRoutePlanService._freeze_one_shot_in_transaction()`](../../holdspeak/services/inference_route_plan_service.py) | Resolves the subject assignment, freezes the route plus operation request plan, including serialized request and preflight evidence. |
| 4 | [`InferenceFallbackController.start_execution_in_transaction()`](../../holdspeak/services/inference_fallback_controller.py) | Reconstructs the frozen pair and starts the execution state machine with its frozen budgets. |
| 5 | [`RoutedInferenceCoordinator.execute()`](../../holdspeak/services/inference_adoption_service.py) | Reserves the next legal attempt, reconstructs the frozen serialized request, and creates an `InvocationRequest`. |
| 6 | [`InferenceRunner.invoke()`](../../holdspeak/kernel/inference_runner.py) | Claims one admitted `inference.invoke@1` child for the frozen deployment revision, issues dispatch context, calls the adapter, and closes the child receipt. |
| 7 | [`InferenceFallbackController`](../../holdspeak/services/inference_fallback_controller.py) | Settles immutable Runner evidence, elects the route outcome, and reconstructs the `RouteExecutionReceipt`. |
| 8 | [`RecipeService.run()`](../../holdspeak/services/recipe_service.py) | Finalizes only the elected winner's projection and returns it with `route_execution_receipt`. |

For a failed primary, the controller may reserve another attempt on the same
leg when the frozen retry policy permits it. Otherwise it may reserve the next
frozen fallback leg when that policy permits it. It never rereads Assignments.
Each physical child has its own receipt. The route receipt records the elected
outcome over those children.

## 7. Controller, fallback, and receipts

[`InferenceFallbackController`](../../holdspeak/services/inference_fallback_controller.py)
is the sole state machine above the Runner. Callers cannot name a leg,
deployment, ordinal, budget, disposition, or winner. The controller reconstructs
the frozen pair, reserves the next legal child, claims that reservation, binds
the claimed kernel child, writes dispatch intent before physical send, and
settles immutable Runner receipt evidence.

A retry stays on its route leg and is bounded by the frozen per-leg policy. A
fallback advances to the next frozen leg only for a permitted disposition. A
preflight-unavailable leg terminalizes unless the frozen context-overflow rules
permit a larger executable fallback. The `RouteExecutionReceipt@1` is a
privacy-safe route-level election. It does not replace individual physical child
receipts.

## 8. The `InferenceRunner` waist

[`InferenceRunner`](../../holdspeak/kernel/inference_runner.py) has a narrow
physical job. For one frozen `InvocationRequest`, it submits, approves, and
claims one `inference.invoke@1` child, binds dispatch context and warrant to the
exact deployment revision, calls the adapter, and durably closes exactly one
terminal receipt. It never resolves current assignments or chooses fallback
legs.

The one-path census in
[`tests/unit/test_one_path_census.py`](../../tests/unit/test_one_path_census.py)
uses fail-closed AST checks to keep provider dispatch from growing alternate
doors. The route authority and controller decide logical work. The Runner owns
one physical provider attempt.

## 9. ToolTurn is a constrained extension, not an alternate router

[`ToolTurnFoundationService`](../../holdspeak/services/tool_turn_service.py)
composes a `tool.turn` parent, an exact tool-qualified route bundle, a private
capability lease, and
[`ToolTurnController`](../../holdspeak/services/tool_turn_controller.py). Model
steps still use the installed fallback controller and Runner. Tool calls are
broker-admitted children through `BrokerToolCallPort`, not direct model-side
execution.

`agent.tool_turn` requires a deployment-bound capability manifest with a
qualified structured-tool palette and dialect, plus the process-bound Tool
Capability Foundation. The compatibility check is in
[`InferenceAssignmentService`](../../holdspeak/services/inference_assignment_service.py).
Every continued or fallback model route must remain tool-qualified. The
controller's closed disposition rules govern whether it continues, falls back,
settles, stops, or becomes indeterminate.

`chat.turn` (formerly `recipe.chat`, retired in Phase 151) is the first
adopter. It probes the `agent.tool_turn` route and uses the narrow Agent turn
facade only when that route is ready. There is no broad model `call_tool`
transport.

The extension preserves the same division of labour as ordinary routed work.
The parent bundle freezes the candidate model route before the turn begins. The
lease limits which capability and tool palette the controller may use. A model
step receives its own operation request plan, controller execution, Runner
child, and route receipt. A tool child is a separate broker operation with its
own admissibility and receipt. The controller, rather than a provider response,
orders those facts and determines the next lawful action.

## 10. Request-level structured output (meeting intelligence)

Meeting intelligence sends a `response_format` of type `json_schema` on every
cloud or endpoint request. The schema is derived from `INTEL_SCHEMA` in
`holdspeak/intel/parsing.py` and wrapped by `intel_response_format()` into the
OpenAI-compatible `{type: "json_schema", json_schema: {name, strict, schema}}`
envelope. Both the prompt and the response_format reference the same constant.

The schema carries the named-owner shape: `owner` is `string | null`, where the
string is a literal person name as spoken in the transcript, or one of two
reserved tokens (`Me`, `Remote`). Downstream consumers treat `owner` as an
opaque string. Only the prompt and the schema constant define the reserved set.

When an endpoint rejects `response_format` with HTTP 400, the engine records
the dialect in `_COMPAT_NO_RESPONSE_FORMAT` (the same pattern as the
`max_completion_tokens` dialect set) and raises a `ProviderCompatibilityRetry`
signal with reason `"no_response_format"`. The runner turns this into a second
admitted child whose request omits `response_format`. The first child's receipt
records the 400; the second child gets one physical request and its own receipt.
`forget_endpoint_dialects()` clears both dialect sets (used in tests; a fresh
process starts empty). The prompt's JSON instruction and the `_extract_json`
recovery heuristic remain the safety net when structured output is absent.

## 11. Plugin capability skip at claim planning (Design A)

`_plan_installed_plugin_members` in `holdspeak/db/intel.py` freezes the
installed plugin set from the composed capability registry. A plugin capability
whose assignment cannot be frozen (the probe returns `no_assignment` from
`resolve_route_plan_for_feature`) is excluded from the bound claim with a
receipt (`plugin_chain_skipped`), never a terminal refusal. Core capabilities
(`meeting.deferred_analysis`, `meeting.bookmark_label`, `meeting.auto_title`)
remain strict: a missing assignment is terminal.

The skip is recorded in the frozen route metadata under `plugin_chain_skipped`,
an array of `{plugin_id, capability_id, reason}` entries. The frozen
`plugin_chain` excludes skipped plugins so the execution path never encounters
a member-missing refusal. The binder's `prepare` stays strict and untouched,
and `router.py`'s chain stays honest (it sees only what was frozen).

The probe uses `resolve_route_plan_for_feature` through the same path the
binder uses, reading persisted assignment heads only (no Config, no live host).
`_plugin_assignment_reachable` returns `False` on `no_assignment`; any other
validation error propagates.

## 12. One-way migration and the census/sync fences

A migration reads known legacy bytes once, writes exact canonical assignments
and source proof in one transaction, then commits a family marker. After that
marker, the feature does not dual-read a legacy pointer. Startup owns family
migration through
[`RoutedInferenceCoordinator`](../../holdspeak/services/inference_adoption_service.py)
and
[`holdspeak/kernel/runtime.py`](../../holdspeak/kernel/runtime.py). Recipe
writes and runs fence retired selectors after the relevant marker exists in
[`RecipeService`](../../holdspeak/services/recipe_service.py).

The execution census is distinct from route authority and feature adoption
guards. The census protects the single Runner path. Assignment, route-plan,
controller, and adopter fences protect who may freeze and execute work.

Router state is hub-local. `SYNC_REGISTRY` intentionally excludes profile and
binding authority, assignments, route and operation plans, execution and attempt
state, receipt attestations, acquisition, readiness, probes, and invocations.
[`sync_service.py`](../../holdspeak/services/sync_service.py) names those
forbidden buckets so an old or hostile peer receives a refusal rather than a
partial replica.

## 13. Owner surfaces and transport parity

| Owner question | Canonical service | HTTP and MCP twin |
|---|---|---|
| What models are available? | [`ModelLibraryApplicationService`](../../holdspeak/services/model_library_service.py) | [`model_library.py`](../../holdspeak/web/routes/model_library.py) and [`mcp/families/model_library.py`](../../holdspeak/mcp/families/model_library.py) |
| Which compatible ordered chain will work use? | [`InferenceAssignmentService`](../../holdspeak/services/inference_assignment_service.py) | [`inference_assignments.py`](../../holdspeak/web/routes/inference_assignments.py) and [`mcp/families/inference_assignments.py`](../../holdspeak/mcp/families/inference_assignments.py) |

Model Library changes availability and proves assignment heads are unchanged.
Assignments writes or clears canonical sparse chains. HTTP and MCP call the same
service authorities. Read [the API surface](../API_SURFACE.md) for route names
and [the MCP sidecar](../MCP_SIDECAR.md) for tool schemas. Neither is a second
routing mechanics reference.

## See also

- [Backend runtime](ARCHITECTURE_BACKEND_RUNTIME.md): operation-kernel composition.
- [Models](../MODELS.md): owner setup for Model Library and Assignments.
- [Plugin Authoring](../PLUGIN_AUTHORING.md): declared plugin and typed-result work.
- [MCP sidecar](../MCP_SIDECAR.md): owner transport tools and resource schemas.
- [Security & Privacy](../SECURITY.md): custody and egress posture.
- [API surface](../API_SURFACE.md): generated HTTP route inventory.
