# HS-143-15 — Intelligence Router repo-wide docs plan

## Ground truth and boundary

This is a documentation-only story. The shipped source on
`feat/hs143-11-transport-parity` is the authority for every factual sentence;
the Story 07–13 progress/evidence record is only the shipping audit trail. The
new document must use stable module paths in prose and reserve line references
for this implementation plan and review checklist, because implementation line
numbers will move.

## 1. Obligation register

| Acceptance obligation | Documentation slice | Proof of completion |
|---|---|---|
| Explain every Problem mechanic with a live owning-module pointer. | S1, new internal architecture document. | Section-by-section code read against the sources in the architecture below; all Markdown links resolve. |
| Teach assignment lookup, freeze, execution, fallback, and receipt as one coherent chain. | S1, with the Recipe run as the document spine. | A cold-reader trace audit follows each named method and reaches the elected route receipt without consulting a roadmap file. |
| Cover ToolTurn, migration/marker law, census guards, owner surfaces/transports, and sync exclusion. | S1. | The completed document has distinct, bounded sections for all five, each pointing at live authority. |
| Replace stale or partial entry-point accounts with one canonical deferral. | S2, entry-point updates and generated API framing. | The stale-claims checklist below is exhausted; retained text is a product/setup summary, not a second routing specification. |
| Preserve document style and user-facing voice. | S1 and S2. | `DOCS_STYLE.md` link/vocabulary/See-also rules pass; README, MODELS, Plugin Authoring, and MCP prose follows `POSITIONING.md`. |
| Prove documentation follows shipped code rather than plans. | S3, trace verification. | Reviewer records the source path/function visited for every Recipe trace hop and runs the relevant docs/census tests. |

## 2. New document architecture

Create `docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md` as the single
mechanics reference. It is an internal architecture document, not an owner
setup guide. Open with a short lede, a reading-order diagram or compact chain,
and a one-paragraph division of labor: **Model Library makes models available;
Assignments choose a compatible ordered chain; the router freezes and executes
one immutable attempt at a time.** End with `## See also` links to Backend
Runtime, Models, Plugin Authoring, MCP Sidecar, Security, and the API surface.

| Section in reading order | What it must teach | Shipped-code ground truth |
|---|---|---|
| **1. Scope, nouns, and ownership** | Define capability, profile, binding, deployment revision, assignment, route plan, operation request plan, execution, attempt, and receipt. State that configuration is local authority, never a mutable execution instruction. | Registry types at `holdspeak/inference_capabilities.py:251-729`; model-profile revision/binding service at `holdspeak/services/model_profile_service.py:205-927`; plan service header and schemas at `holdspeak/services/inference_route_plan_service.py:1-123`. |
| **2. Capability registry before model resolution** | Explain the sealed process registry, exact capability/retry-policy revisions and hashes, owner projection, plugin capability inclusion, and the rule that `require()` precedes profile resolution. Do not enumerate every capability in prose. | `InferenceCapabilityDefinition` and registry composition/lookup, `holdspeak/inference_capabilities.py:379-729, 1031-1215`; owner HTTP/MCP projection service, `holdspeak/services/inference_capability_service.py:1-36` and `holdspeak/mcp/resources.py` capability resource registration. |
| **3. Model authority and availability are separate** | Explain immutable public ModelProfile revisions plus binding to a deployment revision; private endpoint/key material stays in custody/deployment authority. Then distinguish the Model Library aggregate from assignment writes: library acquisition/connect actions prove assignment heads unchanged. | `ModelProfileService` methods at `holdspeak/services/model_profile_service.py:380-927`; `ModelLibraryApplicationService` contract and commands at `holdspeak/services/model_library_service.py:1-12, 64-236, 401-621`; key custody boundary at `holdspeak/services/profile_key_service.py:19-60`. |
| **4. Sparse assignments and whole-chain precedence** | Teach one-to-four ordered profile entries, compatible-chain validation, no implicit merge/trim, and exact precedence: invocation → subject (`thought`, `workbench`, `agent`, `recipe`, `project`) → capability → group → global. Explain that a subject assignment is capability-specific and that a `Use default` clear re-exposes the next whole chain. | Schema/subject kinds at `holdspeak/services/inference_assignment_service.py:1-60`; scope grammar at `:1420-1517`; chain and compatibility validation at `:1519-1892`; resolver at `:1894-1951`. |
| **5. Freeze: route plan then operation request plan** | Explain the read-only resolve versus atomic freeze distinction. A route plan freezes capability, assignment source/hash, ordered deployment revisions, retry policy, deadline, and preflight. The operation request plan binds private, serialized request/context/budget evidence to that route; reconstruction does not reread mutable heads. | Route resolution and material at `holdspeak/services/inference_route_plan_service.py:209-403`; atomic freeze at `:405-681`; operation-plan freeze/reconstruction at `:898-1298, 1592-1695`; production evidence serialization at `holdspeak/services/inference_adoption_service.py:215-498, 752-786`. |
| **6. Recipe run walkthrough: the canonical spine** | Walk exactly one `RecipeService.run` call from its `recipe.run` subject lookup through admission, frozen pair, execution ID, next-attempt reservation, `InferenceRunner`, post-election projection, and returned `RouteExecutionReceipt`. Make every step a source link and explicitly say editing an assignment after admission affects a later run only. This is the acceptance-critical cold-reader path. | Entry and subject parameters, `holdspeak/services/recipe_service.py:91-140`; admission composition, `holdspeak/services/inference_adoption_service.py:816-887`; physical execution loop, `:1403-1589`; Runner child/claim/dispatch/receipt waist, `holdspeak/kernel/inference_runner.py:145-180, 196-403`; frozen-plan regression proof, `tests/unit/test_phase143_production_adoption.py:98-139`. |
| **7. Controller, fallback, and receipts** | Explain that the controller, not an adopter, reserves the next legal attempt from frozen evidence, binds the child, records dispatch intent, classifies immutable Runner evidence, and elects the winner/terminal receipt. Retry is same leg within policy; fallback is next leg only when the frozen policy permits it; every physical child has its own receipt. | Controller state-machine contract at `holdspeak/services/inference_fallback_controller.py:41-61`; start/reconstruct at `:63-173`; reservation/fallback election at `:175-410`; claim/bind/dispatch/settlement at `:415-740`; receipt schema at `:18-24`. |
| **8. The `InferenceRunner` waist** | Explain its narrow physical role: submit/approve/claim one `inference.invoke@1` child on the frozen deployment revision, attach a dispatch context/warrant, call the adapter, and durably close exactly one terminal receipt. It never resolves current assignments. Describe the canonical one-path census as the guard against alternate provider doors. | `holdspeak/kernel/inference_runner.py:1-75, 145-180, 196-458`; census gateway and fail-closed AST test at `tests/unit/test_one_path_census.py:1-35, 377-487, 649-700`. |
| **9. ToolTurn is a constrained extension, not an alternate router** | Explain parent route bundle, private capability lease, bounded model steps, broker-admitted tool children, model-step receipts, and the qualification law: `agent.tool_turn` requires a valid deployment-bound manifest, qualified structured tools, and the process-bound foundation. Document the closed disposition table and that every continued/fallback model route must be tool-qualified. Name `recipe.chat` as the first adopter; its persisted `RecipeRecord.tools` list is not route authority. | Foundation composition and parent/lease start at `holdspeak/services/tool_turn_service.py:33-180`; lease/controller and disposition law at `holdspeak/services/tool_turn_controller.py:1-123, 253-398, 673-865, 1024-1192`; qualification checks at `holdspeak/services/inference_assignment_service.py:1839-1892`; qualified Recipe chat branch at `holdspeak/services/recipe_service.py:142-214`. |
| **10. One-way migration and the census/sync fences** | Explain migration as read legacy bytes once, write exact canonical assignments and source proof atomically, commit the family marker, then never dual-read the legacy pointer. Explain startup ownership and post-marker refusals/write-through. State router/profile/binding/assignment/plan/execution state is hub-local and explicitly excluded from sync. Separate the execution census from the route-authority/feature adoption guards. | Marker transaction at `holdspeak/services/inference_assignment_service.py:1130-1231, 1233-1384`; family migration/startup orchestration at `holdspeak/services/inference_adoption_service.py:81-92, 2596-2711`; startup composition at `holdspeak/kernel/runtime.py:157-193`; post-marker Recipe fences at `holdspeak/services/recipe_service.py:224-293`; sync exclusion at `holdspeak/services/sync_service.py:32-108`; one-path census above plus `tests/unit/test_phase143_production_adoption.py` and `tests/unit/test_phase143_subject_pointer_migration.py`. |
| **11. Owner surfaces and transport parity** | Explain only the ownership split and transport twins: Model Library changes availability but not assignments; Assignments writes/clears canonical sparse chains; HTTP and MCP reach the same services. Link readers to API Surface for route names and MCP Sidecar for tool schemas rather than restating endpoints. | HTTP adapters at `holdspeak/web/routes/model_library.py:28-175` and `holdspeak/web/routes/inference_assignments.py:27-110`; MCP twin dispatchers at `holdspeak/mcp/families/model_library.py:110-270` and `holdspeak/mcp/families/inference_assignments.py:113-190`; service authority above. |

The Recipe walkthrough should be prose plus a numbered source-linked table, not
a broad historical narrative. Its minimum hops are: `RecipeService.run()` →
`RoutedInferenceCoordinator.admit()` → production evidence stage → atomic route
and operation-plan freeze → `InferenceFallbackController.start_execution()` →
`RoutedInferenceCoordinator.execute()`/`reserve_next_attempt()` →
`InferenceRunner.invoke()`/one claimed `inference.invoke@1` child → durable
settlement/elected `RouteExecutionReceipt` → projection finalization. Include a
small side branch for a failed primary: controller reserves the permitted retry
or next frozen fallback leg; it does not reread Assignments.

## 3. Stale-claims inventory and entry-point disposition

| Entry point | Current stale or parallel account (line references are this branch) | Required disposition |
|---|---|---|
| `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` | `:41-48` accurately states part of the old one-path admission rule but points to the pre-router Architecture anchor and omits registry, frozen plans, controller, assignment precedence, and receipts as a chain. | **Rewrite-to-defer.** Retain one compact Backend Runtime boundary statement; link `ARCHITECTURE_INTELLIGENCE_ROUTER.md` as canonical router mechanics. Do not duplicate the new trace. |
| `docs/MODELS.md` | `:13-22, 26-102` teaches config fields, per-consumer direct setup, AI connections, per-job choice, and inline destination-key workflow. `:105-166` makes `Runs on destinations`, Basic/Advanced and point-of-use pickers the routing account. `:168-200` describes superseded setup/selection actions. `:242-263` teaches current-job/group/global ordered lists, not frozen sparse whole-chain precedence. `:271-276` teaches retired fields; `:287-294` says HoldSpeak never downloads weights despite shipped Library download. | **Rewrite owner-facing Models around the shipped Model Library + Assignments surfaces; defer mechanics to the new document.** Keep supported runtime formats and honest readiness limits only where proven. Remove retired settings keys, inline key/destination CRUD instructions, per-job/pointer language, and obsolete endpoint management. Do not turn MODELS into a second architecture spec. |
| `docs/API_SURFACE.md` | `:1-12` correctly says it is generated; its inference/Library/compatibility rows at `:363-371, :485-495, :622-673` are route inventory, not mechanics. Editing the generated Markdown by hand would be overwritten. | **Keep generated inventory; add one generated framing sentence/link** from `scripts/gen_api_surface.py`, then regenerate `docs/API_SURFACE.md` and `docs/api-surface.json`. It must say route semantics/authority live in the new router document, while preserving legacy compatibility rows as factual inventory. |
| `README.md` | `:37-46` presents only the Runner path and old Architecture link. `:147-149`, `:169-179`, `:322-327`, `:484-485`, and `:503-511` still teach pinned-model/destination selection, AI connections, per-job choice, inline key editing, endpoint-centric setup, and destination truth. `:455-470` also has stale sidecar counts and “four” model tools. | **Rewrite-to-defer and trim.** Keep one product-level promise that Settings lets the owner make models available and assign them, with Models as setup guide and the new internal doc as technical detail. Correct counts only after obtaining them from live `mcp` registration. Remove endpoint/destination CRUD and per-job selection teaching. |
| `docs/PLUGIN_AUTHORING.md` | `:3-8, :24-34, :54-65` tells plugin authors to call their configured LLM. `:162-246` gives a direct cached-provider/private `_chat_completion_text` pattern; `:250-271` derives the LLM gate from old config. These are an alternate model-entry account and conflict with registered plugin capabilities/host-issued admitted work. | **Rewrite-to-defer.** Preserve plugin declaration, typed result, rendering, and chain-authoring material, but replace direct provider construction/calls and config gate instructions with the host-issued registered-capability/admitted-route rule. Link the new router doc for execution mechanics; cite the public host interface actually shipped rather than inventing a new plugin API. |
| `docs/MCP_SIDECAR.md` | `:90-113` is good Story-11 parity framing but currently has no canonical-router link. `:237-266` separately teaches direct `InferenceRunner.invoke()` paths, a stale five-tool table, old precedence tiers (`invocation`, `workbench`, `agent`, `global`), and settings-side destination reassignment. | **Keep the accurate Library/Assignment twin summaries and add a deferral link. Rewrite `:237-266` to a short receipt/least-authority statement that defers route mechanics to the new doc.** Do not duplicate chain precedence or runner internals here. |

Also sweep the generated/index links that these entry points name. In particular,
`README.md` must stop sending readers to the endpoint-centric
`INFERENCE_TARGETS.md` as the model-routing authority; this story does not need
to rewrite that out-of-scope guide, but may remove or relabel the stale README
entry so it cannot compete with the new canon.

## 4. Implementation slices

### S1 — Write the canonical internal architecture document

Add `docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md` using the eleven-section
outline above. Write against the exact source links in the ground-truth table,
not Story plan prose. Include the Recipe run walkthrough, ToolTurn foundation
and `recipe.chat` adoption, migration markers, guards, sync exclusion, and the
owner-surface transport split. Use stable module paths in the published prose;
include hashes/type names where they explain immutability, not volatile source
line numbers. Add a `## See also` footer following `DOCS_STYLE.md`.

### S2 — Make every entry point defer, then regenerate API inventory

Update Backend Runtime, MODELS, README, Plugin Authoring, and MCP Sidecar in the
dispositions above. Extend `scripts/gen_api_surface.py` to emit the one
canonical-router deferral in the generated preamble, run the generator, and
commit its generated artifacts. Keep owner setup in MODELS, but make the
Library/Assignments split explicit and route mechanics a link. This slice has
no product-code, web-surface, schema, API, or MCP behavior changes.

### S3 — Trace and vocabulary verification

A separate reviewer follows the finished Recipe walkthrough against the live
functions in order, records pass/fail for every hop, and checks all module links
exist. Run:

```bash
uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_api_surface.py
uv run pytest -q tests/unit/test_one_path_census.py tests/unit/test_phase143_production_adoption.py tests/unit/test_phase143_tool_turn_boundaries.py
uv run python scripts/gen_api_surface.py
# rerun test_api_surface after generation; inspect git diff before accepting it
uv run pytest -q tests/unit/test_api_surface.py
```

Then run a scoped, reviewed stale-vocabulary sweep over only user/developer
entry docs (not `pm/roadmap`, source, or generated route tables):

```bash
rg -ni -e 'download[[:space:]]*(&|and)[[:space:]]*use' \
  -e 'inline[[:space:]]+(target|destination|key)' \
  -e 'per[-[:space:]]job[[:space:]]+(pointer|selector|target)' \
  -e 'destination[[:space:]]+(crud|picker|selector)' \
  README.md docs/MODELS.md docs/PLUGIN_AUTHORING.md docs/MCP_SIDECAR.md \
  docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md
```

Expected result is no obsolete teaching. Any unavoidable quoted UI/code/API
compatibility string must be reviewed case-by-case, not blanket-excluded. The
new internal document may name historical compatibility only in its migration
section, never as a current owner instruction.

## 5. [ORCH-CALL] decisions

1. **Depth budget — recommend 1,800–2,500 words plus one compact trace table and
   one compact authority table.** The full chain needs real depth, but copying
   API schemas, every capability, or all fallback states would create the next
   parallel manual. Stable links carry the extension depth.
2. **MODELS shape — recommend a substantial owner-guide rewrite, not a
   trim-to-link.** Its central mental model is retired (`destination` CRUD and
   point-of-use choice). Retain practical model acquisition/provider/readiness
   help, lead with Model Library then Assignments, and defer router mechanics.
3. **Recipe trace location — recommend the new internal document, not a
   companion.** It is the acceptance-critical proof of how the router works;
   separating it recreates the archaeology problem. Keep it anchored as
   `#recipe-run-from-assignment-to-receipt` so entry points and future audits can
   deep-link it.
4. **API Surface framing — recommend generator-owned, one sentence only.** It
   keeps a regeneration from erasing the canonical deferral without turning a
   route inventory into narrative API documentation.

## 6. Risks and controls

| Risk | Control |
|---|---|
| Documentation drifts as source moves. | Published prose cites stable module paths and named public/service methods; this plan's line references are review aids only. |
| MODELS becomes an architecture duplicate again. | Enforce the owner-setup versus mechanics boundary in S2 and link the canonical doc at first routing mention. |
| Generated `API_SURFACE.md` loses a manual edit. | Change the generator, regenerate, and retain the API snapshot test. |
| A Recipe trace silently follows an obsolete adapter. | S3 requires a literal code-follow against `RecipeService.run`, coordinator, controller, and Runner on the final branch. |
| Legacy vocabulary survives in a user-facing entry point. | S3 grep is a review gate. Promote its narrow, reviewed patterns to a guard candidate in Story 14 rather than treating grep output as a permanent test today. |
| ToolTurn prose falsely makes it a general agent tool API. | Name its lease/controller/model-step qualification law and `recipe.chat` adopter, then state that no broad model `call_tool` transport exists. |
| Sync wording accidentally promises router state replication. | Cite the explicit `SYNC_REGISTRY` absence and `_HUB_LOCAL_FORBIDDEN_BUCKETS` refusal list. |

## 5b. Orchestrator dispositions (2026-08-27)

All four recommendations ACCEPTED as written, decided by the
orchestrator as tie-breaker: 1,800–2,500-word canonical doc with the
Recipe-run trace anchored inside it
(`#recipe-run-from-assignment-to-receipt`); MODELS.md gets the
substantial owner-guide rewrite (its retired mental model dies —
Library-then-Assignments leads); API_SURFACE deferral is one
generator-owned sentence via scripts/gen_api_surface.py. Build: all
three slices in one round; the trace-verification pass is mandatory
before the round reports (the worker follows its own doc's trace
against live code, and the stale-vocabulary greps must run clean).
The forbidden-vocabulary grep is handed to Story 14 as a guard
candidate.
