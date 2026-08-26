# Generated inference/capability census

**Story:** HSEGHS001HS104-143-01

**Regenerated:** 2026-08-25 on `feat/hs143-10-placement-adoption`

This is the checked-in baseline for the Phase 143 route migration. Its
machine-readable fixture is
[`tests/unit/test_phase143_inference_capability_census.py`](../../../../../tests/unit/test_phase143_inference_capability_census.py).
It consumes the Phase 131 AST census rather than a broad text search. The
fixture has one literal `path:line / scope / target / kind` entry for each
site; moving a site or adding a second execution-shaped expression in an
already admitted scope fails the focused test until it receives an explicit
capability and source-owner classification.

## Current result

102 Python production model-shaped sites are registered. There are 14 direct
Python provider/model leaves and **zero Python legacy bypasses**. The Phase 131
findings ledger is empty. `InferenceRunner` remains the Python physical
admission waist; all Python direct leaves are context-gated adapters or
dispatch closures reached from an admitted child. The seven Swift physical
leaves remain separately inventoried below as **HELD** by the 2026-08-25 owner
ruling; the Python zero is never represented as a Swift zero.

| Proposed capability | Sites | Current source owner |
|---|---:|---|
| `agent.tool_turn` | 2 | `services.agent_turn_service` |
| `internal.inference.dispatch` | 37 | runner, target factories, MeetingIntel provider adapters |
| `internal.speech.runtime_assembly` | 16 | speech-session/dictation runtime assembly |
| `meeting.auto_title` | 2 | `meeting_session` |
| `meeting.bookmark_label` | 2 | `meeting_session` |
| `meeting.deferred_analysis` | 1 | `meeting_session.deferred_bound` |
| `meeting.live_analysis` | 1 | `meeting_session` |
| `project_doc.suggest_update` | 3 | `project_doc_suggestions` |
| `speech.intent_classify` | 7 | `speech_session` |
| `speech.preload` | 1 | `speech_session.transcription` |
| `speech.punctuate` | 1 | `speech_session` |
| `speech.rewrite` | 11 | `speech_session` |
| `speech.target_classify` | 3 | `target_profile` |
| `speech.transcribe` | 15 | `speech_session.transcription` |

`internal.inference.dispatch` and `internal.speech.runtime_assembly` are
non-assignable proposed implementation IDs. They mark shared gateway/factory
work, not a generic owner-facing model task. A parent caller supplies the
eventual typed capability at admission; Story 02 replaces these proposal IDs
with registry definitions where a persisted capability is required.

### HS-143-08 current closure anchors

The reviewed literal fixture records the current AST anchors for the extracted
meeting closures. HS-143-08/C1 classifies the three stored-route dispatch
closures in `meeting_session/deferred_bound.py` as `L:` execution leaves:
`bound_analysis_dispatch.call` → `meeting.deferred_analysis`,
`bound_bookmark_label_dispatch.call` → `meeting.bookmark_label`, and
`bound_auto_title_dispatch.call` → `meeting.auto_title`. They are exact frozen
bundle members reached only after child admission, not queue-orchestration
allowlist entries. The legacy deferred closures remain in
`meeting_session/deferred_admission.py`; this changes locations, not the three
capabilities or their `meeting_session` source owner.

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
| `transcribe.py:284` | MLX model preload `get_model` | `speech.preload` |
| `transcribe.py:294` | silent-audio MLX warmup `transcribe` | `speech.transcribe` |
| `transcribe.py:339` | MLX Whisper `transcribe` | `speech.transcribe` |
| `transcribe.py:421` | faster-whisper `transcribe` | `speech.transcribe` |

The first four rows are reached through a runner-built `MeetingIntel` and its
canonical adapter. Dictation rows are reached through the admitted dictation
runtime; the two Whisper preload/warmup rows and both transcription backends
run under `TranscriptionAdmission`, which admits an `inference.invoke@1` child
before their callback can execute. The fixture asserts each physical leaf is a
Phase 131 `allowlist` site and that its recorded admission is `InferenceRunner`.

## Product entrances into the runner

These are the four production references to `InferenceRunner.invoke`, including
a first-class bound method reference. The exact fixture fails on any new
`.invoke` expression, so a product service cannot inherit review merely by
calling the runner directly.

| Source location | Proposed capability provenance | Source owner |
|---|---|---|
| `kernel/mesh_local_runner.py:232` | dynamic: frozen mesh dispatch-offer capability | `kernel.mesh_local_runner` |
| `services/ask_service.py:120` | `internal.semantic_dispatch`; exact capability supplied by semantic caller | `services.ask_service` |
| `services/inference_adoption_service.py:1551` | dynamic: frozen `InferenceRoutePlan` capability | `services.inference_adoption_service` |
| `speech_session/child.py:181` | dynamic: frozen `SpeechSessionPlan` capability | `speech_session.child` |

The dynamic rows are provenance descriptors, not fake registry IDs: their
stored plan or signed offer supplies the typed capability at admission. Story
143-10 product services are absent by design: they call the coordinator rather
than `InferenceRunner.invoke`.

## Shared semantic callers

`AskService._invoke`, `RecipeService._invoke`, and
`SequenceWorkflowService._invoke` are shared helpers, not capabilities. The
semantic caller census is therefore separate from the 13 runner entrances and
walks every production Python module (including direct constructors, service
factories, local aliases, and Refinement's injected Ask factory) before Story 02
routes it. A synthetic new Ask/Recipe caller is a fail-closed test mutation.

| Source location | Capability | Source owner |
|---|---|---|
| `mcp/families/ask.py:146`, `web/routes/primitives/ask.py:49` | `ask.answer` | Ask transports |
| `services/refinement_coordinator.py:328` | `thought.interview` (question-or-synthesis result branch) | refinement coordinator |
| `mcp/tools.py:651`, `web/routes/primitives/recipes.py:100` | `recipe.run` | Recipe transports |
| `mcp/tools.py:655`, `web/routes/primitives/recipes.py:115` | `recipe.chat` | Recipe transports |
| `services/sequence_workflow_service.py:133` | `sequence.step` | Sequence service |
| `services/sequence_workflow_service.py:186` | `workflow.node` | Workflow service |

Refinement is one `thought.interview` capability. Its sealed result contract can
be the next interview question or a terminal synthesis; `thought.synthesis` is
not separately routable today. It must not be reduced to `ask.answer` merely
because it invokes `AskService`.

## Apple Swift scope — HELD by owner ruling

Apple source remains in the physical-leaf scanner, but is out of Story 143-10
scope by the owner's 2026-08-25 ruling. The seven physical leaves below are
**HELD**. They are not Python `InferenceRunner` work, are not counted as zero,
and must never be deleted as bookkeeping. A future Swift phase owns bridge or
recreation work.

| Swift leaf | Proposed capability | Current disposition |
|---|---|---|
| `InferenceLlama/LlamaProvider.swift:124` | `apple.local_completion` | HELD — owner ruling 2026-08-25 |
| `Providers/Inference/OpenAIEndpointProvider.swift:48` | `apple.endpoint_completion` | HELD — owner ruling 2026-08-25 |
| `Providers/Inference/StructuredOutput.swift:64` | `apple.structured_output` | HELD — owner ruling 2026-08-25 |
| `Providers/Desktop/MeshServeWorker.swift:99` | `apple.mesh_serve` | HELD — owner ruling 2026-08-25 |
| `RuntimeCore/Companion/CoderAnswer.swift:109` | `apple.coder_answer` | HELD — owner ruling 2026-08-25 |
| `RuntimeCore/Workbench/BlueprintInterpreter.swift:333` | `apple.workbench.blueprint` | HELD — owner ruling 2026-08-25 |
| `RuntimeCore/Workbench/WorkflowRunner.swift:338` | `apple.workbench.workflow` | HELD — owner ruling 2026-08-25 |

The scanner catches every Swift `.complete(` receiver (including `fallback`)
and every `URLSession.data(for:)` open under `Providers/Inference`; synthetic
mutations prove that an uncatalogued physical leaf fails closed. The separate
surface scanner continues to require zero executable Swift retry/fallback
policy branches.

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
