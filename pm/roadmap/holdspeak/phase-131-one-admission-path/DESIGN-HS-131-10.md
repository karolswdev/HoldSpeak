# HS-131-10 design — The one-path fence

**Status:** RATIFIED-AS-AMENDED (Sol, 2026-08-11) — the five amendments in the Sol ruling below are binding
**Decision boundary:** this is executable test machinery, not another runner. It proves that every physical model dispatch has one admitted `inference.invoke@1` child and terminal receipt, and fails closed when a new door is named.

## Context

HS-131-02–09 establish `InferenceRunner.invoke()` as the generic admission path, frozen revisions, trusted children, per-kind projections, and cancellation-safe terminal receipts. A shared helper is insufficient if a product module can construct an engine, open a stream, run Whisper, or relay to mesh itself. This story extends the literal, source-census house style in `test_gate_chokepoint.py`, the function-identity tracing pattern in `test_inference_kernel.py`, and the AST classifier/ledger style in `test_kernel_effect_fence.py`.

## 1. One executable census

Add `tests/unit/test_inference_one_path_fence.py`. It walks production `holdspeak/**/*.py` with `ast` (not grep): resolve import aliases and dotted calls, record path/line/enclosing function/target, and classify only executable forms: SDK client construction; completion/create and streaming opens; `run_prompt`; provider fallback; `MeshRelayIntel` relay; local runtime/model load; and `Transcriber`/backend `.transcribe`. Imports, annotations, config strings, and availability probes are not sites.

The test owns a literal, one-entry-per-line `ADAPTER_ALLOWLIST: dict[(path, function), justification]`; it is deliberately boring to review. Each listed function must both receive an opaque runner-issued admitted invocation context (or its unforgeable warrant-bearing equivalent) and reject a missing/invalid one before construction/dispatch. The AST test verifies that requirement structurally; focused runtime tests prove rejection. No route, command, plugin, product surface, or domain service is admissible.

Exact initial allowlist (the implementer must make each context requirement true, rather than grandfathering it):

1. `holdspeak/kernel/inference_runner.py:InferenceRunner.invoke` — only child admission/claim and engine-factory entrance.
2. `holdspeak/kernel/inference_runner.py:InferenceRunner._dispatch` — only adapter dispatch/causally linked egress entrance.
3. `holdspeak/inference_targets.py:local_pinned_meeting_intel` and `build_intel_for_revision` — frozen-revision engine construction; require the runner warrant/context.
4. `holdspeak/intel/providers.py:build_configured_meeting_intel` and `build_meeting_intel_for_profile` — provider construction only when called from item 3 with that context.
5. `holdspeak/intel/engine.py:MeetingIntel._ensure_runtime_loaded`, `_ensure_openai_client_loaded`, `_remote_completion`, `run_prompt`, and streaming implementation — physical local/cloud construction and completion behind an adapter-issued context.
6. `holdspeak/intel/mesh_relay.py:MeshRelayIntel.run_prompt` — mesh envelope must carry the same frozen revision and warrant.
7. `holdspeak/kernel/prompt_adapter.py:PromptAdapter.dispatch`, `holdspeak/speech_session/provider.py` dispatch adapter, and `holdspeak/plugins/dictation/runtime_{openai_compatible,llama_cpp,mesh_relay}.py` runtime dispatch methods — adapter-only execution with the same context.
8. `holdspeak/transcribe.py:ModelHolder.get_model`, concrete MLX/faster-Whisper transcribe methods, and `Transcriber.transcribe` — preload and transcription use separately admitted children, never an ambient permit.

A site is green only if it is allowlisted, demonstrably reached from runner context, or is an explicitly named blocked finding below. Anything else fails with `UNREGISTERED_MODEL_EXECUTION path:line scope target`; a synthetic temporary product `OpenAI(...).chat.completions.create(...)`, `engine.run_prompt(...)`, or `.transcribe(...)` must produce that exact named failure. Allowlist edits require a recorded phase decision in the test comment.

## 2. Literal spine and cardinality

Parametrize surface fixtures over **Ask; Recipe run; Recipe chat; Sequence; Workflow; manual Workbench; scheduled Workbench; memory writeback; Rails; Decision; Delivery; voice; meeting live; meeting deferred; dictation pipeline**. (The charter says thirteen but names fifteen distinct entry forms; retain all named forms rather than silently collapsing Recipe, Workbench, or meeting variants.) Each fixture monkeypatches and records identity of the same literal functions: `InferenceRunner.invoke`, `Broker._admit_authority`/trusted-child admission, `Broker.claim`, `InferenceRunner._dispatch`, and `ExecutorPlane._terminal`/receipt persistence. Assert the recorded function objects are the imports from the kernel modules, in that order; wrappers with equivalent behavior do not pass.

At the engine-factory plus `adapter.dispatch` seam, count physical dispatches. For success, refusal, provider failure, cancellation, retry/fallback, and indeterminate recovery assert:

`provider_dispatch_count == admitted inference.invoke child count == terminal inference.invoke receipt count`.

Refusal before dispatch is represented by an admitted, terminal refused child and a zero-dispatch exception only if it did not reach the provider; therefore the harness records an `attempted_dispatch` counter and asserts `actual_dispatch <= children`, while the strict equality is exercised for dispatching scenarios. Retry/fallback creates one child/receipt per attempt. Parent/session receipts and external-egress receipts are separately typed and excluded from child counts; egress is independently asserted causally linked to its invocation child.

## 3. Provenance, hygiene, and terminality

For every child fixture, inspect stored operation/receipt rows: nonempty real parent/session causation, frozen deployment revision selected from the parent plan, authenticated authority basis, capability and attempt ordinal. Submit caller-supplied placement and owner/principal values and assert kernel validation replaces/refuses them.

Extend the existing kernel journal sentinel assertions, rather than duplicate already-proven lifecycle cases: `test_inference_kernel.py` discharges claim/terminal/cancellation/reaper behavior; `test_kernel_effect_fence.py` supplies AST/alias-evasion conventions; `test_intel_egress_invariant.py` remains the local/cloud construction posture guard. The new suite adds missing cross-surface child provenance, journal sentinel scans for prompt, token stream, transcript/dictated body, and audio bytes, and runner-instrumented cardinality. Reuse the existing cancellation/restart tests only after mapping their exact assertions; add only a race fixture that completes a blocked adapter after cancellation/restart and proves no projection/publish occurs and the first terminal receipt is unchanged.

## 4. Census inventory and blocked findings

| Site / family | Disposition |
| --- | --- |
| `kernel/inference_runner.py` gateway/factory/dispatch | authorized runner |
| `inference_targets.py`, `intel/providers.py`, `intel/engine.py` construction/completion/streaming | allowlisted adapters; require runner context |
| `kernel/prompt_adapter.py`, speech and dictation runtime adapters, `intel/mesh_relay.py` | allowlisted adapters; frozen revision+warrant required |
| `transcribe.py` preload and MLX/faster-Whisper execution | allowlisted speech adapter; separate admitted children |
| Meeting/dictation/wake/main/import transcriber callers and migrated surface adapters | migrated callers; context must be threaded, never allowlisted |
| `commands/mesh_serve.py:156` mesh peer `engine.run_prompt` | allowlisted mesh receiver only if it verifies the incoming admitted envelope; otherwise NEW and blocking |
| `services/cadence_service.py:131` `_cadence_llm()` | **NAMED FINDING: cadence** — blocked |
| `meeting_session/session.py` `mir_routing_enabled=True` branch | **NAMED FINDING: dormant MIR** — blocked |
| `web/routes/dictation/_helpers.py:541` dry-run pipeline construction | **NAMED FINDING: dictation dry-run** — blocked |
| `commands/dictation.py:79` pipeline construction | **NAMED FINDING: dictation command** — blocked |
| Plugin `build_configured_meeting_intel` default-provider sites and `web/routes/decisions.py` direct `run_prompt` | migrated only if the AST/context proof reaches runner; otherwise **NEW** and blocking, not an exception |

Draft owner amendments, not implementation work: (1) charter an `HS-131-cadence-admission` story to make cadence planning a bounded service parent with revisioned child calls; (2) charter `HS-131-mir-admission` to either delete the dormant branch or admit every MIR attempt under the meeting session; (3) charter `HS-131-dictation-dry-run-admission` to give dry-run a bounded authenticated/session context or remove provider work; (4) charter `HS-131-dictation-command-admission` to require an explicit authenticated command parent and frozen plan. Until the owner charters each, HS-131-10 is **BLOCKED**, never done.

## 5. Mutation proofs and test matrix

| AC | Focused proof |
| --- | --- |
| Census/finite adapter list | AST fixtures for aliases, direct SDK/run-prompt/transcribe, unregistered adapter, and allowlist context absence |
| Literal spine | fifteen surface parametrization and literal function identity/order |
| Cardinality and parent non-substitution | seam counters across success/refusal/failure/cancel/retry/indeterminate; separate parent/egress counters |
| Provenance/revision/basis | forged placement/principal plus each surface's stored child rows |
| Hygiene/immutable terminality | journal sentinels; blocked adapter cancel/restart then late completion/second receipt |
| Inventory | census snapshot is emitted in evidence; findings remain named and blocking |

Perform three fail-then-green mutations in a disposable working edit: add a direct provider call in a synthetic product module and capture the named census failure; attempt a second changed terminal receipt and capture immutable-receipt failure; put each forbidden sentinel in a journal field and capture the hygiene failure. Remove each edit, rerun the focused suite, and preserve both outputs in evidence. No mutation ships.

## Recorded notes

- The census is intentionally narrower than general effect lint: it protects model execution, not all network or subprocess code.
- “Context required” is semantic, not a parameter-name trick: the test must reject a hand-built/null token and prove it came from the claimed runner child.
- The grep census found construction references and execution candidates; only AST-classified executable forms enter the ledger, preventing comments/imports from becoming noisy false doors.

## Open questions for Sol

1. Confirm the strict equality wording for pre-dispatch refusal: should the AC count admitted attempts or actual provider dispatches? This design records both so neither is hidden.
2. Rule whether `commands/mesh_serve.py:156` is a verified mesh adapter receiver or a new unadmitted execution site.
3. Rule the charter’s “thirteen” versus its fifteen named surface forms; this draft tests every named form.
4. Confirm whether the plugin default-provider and Decisions call sites already carry the new runner context; if not, they are new blockers, not additions to this allowlist.

## Sol ruling

**Verdict: RATIFY-AS-AMENDED.** The architecture is right; five amendments
close census/cardinality holes that would let a door stay open.

### Amendments (binding)

1. **Separate the gateway from its consumers**: a literal
   `AUTHORIZED_GATEWAY` (InferenceRunner.invoke + _dispatch) distinct from
   `ADAPTER_ALLOWLIST`; every allowlisted factory/adapter validates an
   opaque context bound to the claimed operation, frozen revision,
   destination, and attempt ordinal — missing/null/hand-built/
   wrong-operation/wrong-revision/wrong-attempt all refuse before
   construction or dispatch (a parameter named `warrant` is insufficient).
2. **Census callable references + the complete physical vocabulary**:
   cover bound-method references passed as values
   (`asyncio.to_thread(intel.run_prompt, ...)`,
   `chat_fn = intel._chat_completion_text`), indirect sender invocation,
   `_chat_completion_text`/`_chat_completion_stream`,
   `_ensure_local_model_loaded`, `create_chat_completion`/
   `create_completion`, runtime classify/rewrite, all Whisper
   preload/warmup/transcribe leaves, and ALL engine/runtime factories
   including `speech_session/revision_target.py:rebind` (which must become
   a context-requiring adapter factory, not an unledgered constructor).
3. **Count physical leaves and split refusal cohorts**: instrument the
   actual SDK/local-model/mesh/Whisper leaves; assert
   `child_operations == terminal_child_receipts` for every attempt and
   separately `physical_leaf_attempts == dispatched_children <=
   child_operations`; a pre-dispatch refusal proves one child, one refused
   receipt, ZERO physical attempts; each physical attempt (incl. the
   OpenAI compatibility fallback's second `.create` inside one
   adapter.dispatch) has its own child and receipt.
4. **Expand the blocking findings package**: beyond the four known
   findings, add — the mesh receiver (`commands/mesh_serve.py:execute`
   accepts a hand-built job; nonempty warrant fields do not authenticate),
   the legacy plugin default-provider family (fourteen builtin
   `_cached_provider` sites + `plugins/segment_probe.py`),
   `web/routes/decisions.py`'s bound `run_prompt`, the dormant
   `services/delivery_service.py:prepare_pr_review` factory; classify
   `build_intel_for_target` as a legacy uncontextual factory, never an
   adapter exception. Draft owner-story shapes: mesh receiver admission
   (cryptographic warrant verification or a node-side runner);
   plugin default-provider admission; Decision admission (frozen-revision
   child under an authenticated Decision parent); Delivery legacy factory
   (delete or migrate).
5. **Every mutation proves the intended guard fired**: green baseline →
   the exact mutated site/persisted row → the exact expected NAMED failure
   → final green; receipt-immutability mutations reread the original
   receipt byte-for-byte; the provider mutation set includes at least one
   first-class-callable form.

### Open-question rulings

1. Pre-dispatch refusal: count the attempt + its receipt; zero physical
   dispatches; strict equality applies to the dispatched cohort.
2. `commands/mesh_serve.py:156` is a NEW unadmitted execution site
   (finding).
3. Test all FIFTEEN surfaces; the charter's "thirteen" is a miscount —
   named forms control.
4. Plugin and Decisions sites do NOT carry runner context today
   (findings, not allowlist entries).

### Sol recorded notes

- `build_intel_for_revision(..., warrant=...)` forwards the warrant
  through only one branch today; implementation must bind context through
  EVERY branch.
- Allowlist entries name function scopes individually — group labels are
  not reviewable fence entries.
- No additional provider family beyond OpenAI-compatible, llama.cpp,
  mesh, MLX Whisper, faster-Whisper surfaced; the material omissions are
  indirect callable forms and uncontextual factories.

### Orchestrator disposition

All five design amendments ADOPTED. Implementation expanded the ledger to
ELEVEN families: the ruled eight plus the legacy uncontextual factory, the
parallel live meeting engine, and bookmark auto-label. On 2026-08-12 the owner
accepted the complete ledger, chartered HS-131-13 through HS-131-17, and
authorized the verified blocked checkpoint to ship. Each family remains a
finding, never an exception; HS-131-10 cannot close until the amendment wave
deletes or admits every pinned site and the census returns zero findings.
