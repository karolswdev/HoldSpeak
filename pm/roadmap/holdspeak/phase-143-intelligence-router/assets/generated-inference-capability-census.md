# Generated inference/capability census

**Story:** HSEGHS001HS104-143-01

**Captured:** 2026-08-21

This is the checked-in baseline for the Phase 143 route migration. Its
machine-readable fixture is
[`tests/unit/test_phase143_inference_capability_census.py`](../../../../../tests/unit/test_phase143_inference_capability_census.py).
It consumes the Phase 131 AST census rather than a broad text search. The
fixture has one literal `path:line / scope / target / kind` entry for each
site; moving a site or adding a second execution-shaped expression in an
already admitted scope fails the focused test until it receives an explicit
capability and source-owner classification.

## Current result

99 Python production model-shaped sites are registered. There are 14 direct
Python provider/model leaves and **zero Python legacy bypasses**. The Phase 131
findings ledger is empty. `InferenceRunner` remains the Python physical
admission waist; all Python direct leaves are context-gated adapters or
dispatch closures reached from an admitted child. Apple has seven separately
inventoried legacy physical leaves below; it does not yet use the Python runner.

| Proposed capability | Sites | Current source owner |
|---|---:|---|
| `agent.tool_turn` | 1 | `plugins.intelligence` |
| `internal.inference.dispatch` | 37 | runner, target factories, MeetingIntel provider adapters |
| `internal.speech.runtime_assembly` | 15 | speech-session/dictation runtime assembly |
| `meeting.auto_title` | 2 | `meeting_session` |
| `meeting.bookmark_label` | 2 | `meeting_session` |
| `meeting.deferred_analysis` | 2 | `meeting_session.deferred_admission` |
| `meeting.live_analysis` | 1 | `meeting_session` |
| `project_doc.suggest_update` | 3 | `project_doc_suggestions` |
| `speech.intent_classify` | 6 | `speech_session` |
| `speech.preload` | 1 | `speech_session.transcription` |
| `speech.punctuate` | 1 | `speech_session` |
| `speech.rewrite` | 10 | `speech_session` |
| `speech.target_classify` | 3 | `target_profile` |
| `speech.transcribe` | 15 | `speech_session.transcription` |

`internal.inference.dispatch` and `internal.speech.runtime_assembly` are
non-assignable proposed implementation IDs. They mark shared gateway/factory
work, not a generic owner-facing model task. A parent caller supplies the
eventual typed capability at admission; Story 02 replaces these proposal IDs
with registry definitions where a persisted capability is required.

## Direct physical leaves

Every row below is admitted by `InferenceRunner`; there is no bypass/legacy
adapter exception to carry into the migration.

| Source location | Physical operation | Proposed capability |
|---|---|---|
| `intel/engine.py:273` | local `create_chat_completion` | `internal.inference.dispatch` |
| `intel/engine.py:311` | OpenAI-compatible `chat.completions.create` callback | `internal.inference.dispatch` |
| `intel/engine.py:349` | streaming local `create_chat_completion` | `internal.inference.dispatch` |
| `intel/engine.py:387` | streaming OpenAI-compatible callback | `internal.inference.dispatch` |
| `intel/mesh_relay.py:252` | relay `run_prompt` | `internal.inference.dispatch` |
| `plugins/dictation/runtime_llama_cpp.py:134` | constrained `create_completion` | `speech.intent_classify` |
| `plugins/dictation/runtime_llama_cpp.py:162` | rewrite `create_completion` | `speech.rewrite` |
| `plugins/dictation/runtime_mesh_relay.py:106` | relay `run_prompt` | `internal.speech.runtime_assembly` |
| `plugins/dictation/runtime_openai_compatible.py:141` | classify `chat.completions.create` | `speech.intent_classify` |
| `plugins/dictation/runtime_openai_compatible.py:188` | rewrite `chat.completions.create` | `speech.rewrite` |
| `transcribe.py:241` | MLX model preload `get_model` | `speech.preload` |
| `transcribe.py:251` | silent-audio MLX warmup `transcribe` | `speech.transcribe` |
| `transcribe.py:296` | MLX Whisper `transcribe` | `speech.transcribe` |
| `transcribe.py:378` | faster-whisper `transcribe` | `speech.transcribe` |

The first four rows are reached through a runner-built `MeetingIntel` and its
canonical adapter. Dictation rows are reached through the admitted dictation
runtime; the two Whisper preload/warmup rows and both transcription backends
run under `TranscriptionAdmission`, which admits an `inference.invoke@1` child
before their callback can execute. The fixture asserts each physical leaf is a
Phase 131 `allowlist` site and that its recorded admission is `InferenceRunner`.

## Product entrances into the runner

The physical-site inventory above is not enough on its own: these are the 12
production callers of `InferenceRunner.invoke`, including first-class bound
method references passed to `asyncio.to_thread`. The checked-in fixture fails
on any new `.invoke` expression, so a new service cannot inherit an existing
source owner's review by merely using the runner.

| Source location | Proposed capability provenance | Source owner |
|---|---|---|
| `kernel/mesh_local_runner.py:232` | dynamic: frozen mesh dispatch-offer capability | `kernel.mesh_local_runner` |
| `meeting_session/intel_child.py:193` | dynamic: frozen `MeetingIntelPlan` capability | `meeting_session.intel_child` |
| `rails_observer.py:268` | `background.rails_summary` | `rails_observer` |
| `services/ask_service.py:63` | `internal.semantic_dispatch`; exact capability supplied by the semantic caller | `services.ask_service` |
| `services/cadence_service.py:284` | `background.cadence_draft` | `services.cadence_service` |
| `services/decision_lifecycle_service.py:81` | `decision.promotion_draft` | `services.decision_lifecycle_service` |
| `services/recipe_service.py:52` | `internal.semantic_dispatch`; exact capability supplied by the semantic caller | `services.recipe_service` |
| `services/sequence_workflow_service.py:44` | `internal.semantic_dispatch`; exact capability supplied by the semantic caller | `services.sequence_workflow_service` |
| `services/workbench_runner.py:41` | `workbench.item` | `services.workbench_runner` |
| `services/workbench_service.py:414` | `voice.reference_resolve` | `services.workbench_service` |
| `speech_session/child.py:181` | dynamic: frozen `SpeechSessionPlan` capability | `speech_session.child` |
| `web/routes/delivery_prs.py:252` | `delivery.pr_review_draft` | `web.routes.delivery_prs` |

The three dynamic rows are deliberately provenance descriptors, not fake
registry IDs: their current plan or signed offer chooses a typed capability at
admission. Story 02 must carry that exact capability into its registry/route
plan rather than collapsing the family into one broad assignment.

## Shared semantic callers

`AskService._invoke`, `RecipeService._invoke`, and
`SequenceWorkflowService._invoke` are shared helpers, not capabilities. The
semantic caller census is therefore separate from the 12 runner entrances and
walks every production Python module (including direct constructors, service
factories, local aliases, and Refinement's injected Ask factory) before Story 02
routes it. A synthetic new Ask/Recipe caller is a fail-closed test mutation.

| Source location | Capability | Source owner |
|---|---|---|
| `mcp/families/ask.py:146`, `web/routes/primitives/ask.py:49` | `ask.answer` | Ask transports |
| `services/refinement_coordinator.py:328` | `thought.interview` (question-or-synthesis result branch) | refinement coordinator |
| `mcp/tools.py:533`, `web/routes/primitives/recipes.py:100` | `recipe.run` | Recipe transports |
| `mcp/tools.py:537`, `web/routes/primitives/recipes.py:115` | `recipe.chat` | Recipe transports |
| `services/sequence_workflow_service.py:133` | `sequence.step` | Sequence service |
| `services/sequence_workflow_service.py:186` | `workflow.node` | Workflow service |

Refinement is one `thought.interview` capability. Its sealed result contract can
be the next interview question or a terminal synthesis; `thought.synthesis` is
not separately routable today. It must not be reduced to `ask.answer` merely
because it invokes `AskService`.

## Apple Swift scope

Apple source is in scope for the physical-leaf baseline but is not covered by
the Python `InferenceRunner`. Seven Swift leaves are named **legacy bypasses**
with their migration owner; they must converge on the Phase 143 route/fallback
law before an Apple capability can claim parity.

| Swift leaf | Proposed capability | Exact migration story |
|---|---|---|
| `InferenceLlama/LlamaProvider.swift:124` | `apple.local_completion` | Story 143-10 — Agents/workbenches/recipes adoption |
| `Providers/Inference/OpenAIEndpointProvider.swift:48` | `apple.endpoint_completion` | Story 143-10 — Agents/workbenches/recipes adoption |
| `Providers/Inference/StructuredOutput.swift:64` | `apple.structured_output` | Story 143-10 — Agents/workbenches/recipes adoption |
| `Providers/Desktop/MeshServeWorker.swift:99` | `apple.mesh_serve` | Story 143-10 — Agents/workbenches/recipes adoption |
| `RuntimeCore/Companion/CoderAnswer.swift:109` | `apple.coder_answer` | Story 143-10 — Agents/workbenches/recipes adoption |
| `RuntimeCore/Workbench/BlueprintInterpreter.swift:343` | `apple.workbench.blueprint` | Story 143-06 — fallback-controller migration |
| `RuntimeCore/Workbench/WorkflowRunner.swift:366` | `apple.workbench.workflow` | Story 143-06 — fallback-controller migration |

`WorkflowRunner` and `BlueprintInterpreter` currently retry and may use an
injected fallback provider; those are legacy application-level physical calls,
not evidence of a canonical route-plan controller. Their Story 143-06 migration
must replace that law before Story 143-10 adopts the resulting route.
The scanner catches every Swift `.complete(` receiver (including `fallback`)
and every `URLSession.data(for:)` open under `Providers/Inference`; both have
synthetic mutation proofs.

## Migration implications

* Meeting child closures already distinguish live analysis, deferred analysis,
  bookmark label, and title; route-plan adoption can migrate those without
  collapsing their current admission boundaries.
* Speech has stable typed work (`transcribe`, `preload`, `intent_classify`,
  `rewrite`, `punctuate`); its runtime construction sites stay infrastructure,
  not assignment choices.
* Generic MeetingIntel/provider construction is shared implementation work.
  It must read only a frozen route/deployment provided by the resolver after
  its family crosses; it must never turn into an alternate capability resolver.
* The existing plugin intelligence handle maps to `agent.tool_turn`; its future
  executable route remains gated on Story 09's Tool Capability Foundation.

## Regeneration/check

```bash
uv run pytest -q tests/unit/test_one_path_census.py \
  tests/unit/test_phase143_inference_capability_census.py --tb=short
```

The 143 test is intentionally fail-closed: update the literal fixture, its
classification, semantic caller rows, Swift leaf rows, and this generated
summary in the same reviewed change. A passing test is evidence of current
coverage, not permission to add an unreviewed model call.
