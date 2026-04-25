# Phase DIR-01: Dictation Intent Routing and On-Device Transcript Enrichment

## 1. Phase Charter

### 1.1 Objective

Introduce a real-time, on-device transcript enrichment pipeline for the voice-typing path. After Whisper transcription and before text injection, the transcript flows through an ordered chain of pluggable stages. The first concrete stage is an **LLM-driven intent router** powered by a small Qwen GGUF model running through `llama-cpp-python` (Metal-accelerated on Apple Silicon, CPU/CUDA elsewhere). It classifies the utterance against a user-defined block taxonomy (e.g., "AI prompt buildout", "code exercise", "documentation exercise") and triggers an enrichment stage that injects grounded context drawn from project knowledge bases into the final typed output.

The choice of `llama-cpp-python` over MLX-LM is deliberate: the existing `holdspeak/intel.py` meeting-intel runtime already uses `llama-cpp-python` for GGUF inference. DIR-01 reuses that runtime layer rather than introducing a second on-device LLM stack, which keeps the dependency surface small and makes the pipeline trivially cross-platform from day one. The accepted cost is ~30–50% lower peak throughput on Apple Silicon vs. MLX-LM, which is well inside the latency budget for the 1.5B–3B-class models DIR-01 targets.

### 1.2 Why This Phase Exists

The current typing pipeline (`holdspeak/controller.py:136-180`) treats every transcript identically: `Transcriber.transcribe(audio) → TextProcessor.process(text) → TextTyper.type_text(text)`. There is no way to:

1. Detect the *intent* of an utterance (dictating a prompt to an LLM vs. dictating prose vs. dictating code commentary).
2. Augment the utterance with project-specific grounding before it lands in the destination application.
3. Compose user-defined transformations as a chain without forking the controller.

The existing plugin work in `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` and `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` (MIR-01) targets the **meeting analysis** path with deterministic lexical signal routing producing reviewable artifacts. DIR-01 is the **dictation/typing-side** sibling: live, latency-bound, LLM-driven, transformative (not artifact-producing).

### 1.3 Success Criteria (Phase-Level)

1. The typing path runs through an ordered, configurable pipeline of stages with a stable contract.
2. The on-device LLM runtime is warm-resident, shared across stages, and meets latency targets on Apple Silicon.
3. The intent router classifies an utterance against a user-defined block taxonomy with deterministic, structured output.
4. A matched block triggers a deterministic enrichment stage that injects project-KB-derived context per a user template.
5. Enrichment is opt-in (off by default) and degrades cleanly to plain typing on any failure.
6. Verification evidence is complete and reproducible on the reference Apple Silicon machine.

### 1.4 Reference Hardware

Primary: Apple Silicon (M-series), Metal-accelerated. All latency targets and benchmark commitments are stated against that target. Linux x86_64 is a **secondary supported target** for DIR-01 because `llama-cpp-python` runs there too; it has looser latency expectations (see §9.6) and is verified by integration tests rather than benchmarks.

## 2. Normative Language

`MUST`, `SHOULD`, `MAY` per RFC 2119, matching the convention of `PLAN_PHASE_MULTI_INTENT_ROUTING.md`.

## 3. Scope and Non-Scope

### 3.1 In Scope

1. New `transducer` plugin kind (transcript-in, transcript-out) extending the existing `Plugin` contract.
2. Ordered pipeline executor wrapped around the existing typing path with feature-flagged activation.
3. Long-lived `llama-cpp-python` runtime service exposed to stages via a typed handle, sharing the loader pattern with the existing `holdspeak/intel.py` runtime.
4. Built-in `intent-router` stage with constrained-output classification and pluggable block taxonomy.
5. Built-in `kb-enricher` stage that consumes router output and injects project-KB content per user template.
6. Block-config schema, file-based persistence, and per-project overrides via the existing `project_detector`.
7. CLI/web introspection: dry-run a transcript through the pipeline and inspect each stage's output.
8. Doctor checks for the LLM runtime and model availability.
9. Reference benchmark harness producing evidence on this Mac.

### 3.2 Out of Scope

1. MLX-LM or any second on-device LLM stack. Single backend (`llama-cpp-python`) is a hard rule for DIR-01.
2. Cloud LLM router fallback. Phase DIR-02 candidate.
3. Replacement of the meeting-side MIR-01 routing. DIR-01 and MIR-01 are independent pipelines; they MAY share contracts but MUST NOT share state.
4. External plugin discovery (entry points, third-party packages). Out-of-tree plugins follow the lifecycle proposed in `PLAN_ARCHITECT_PLUGIN_SYSTEM.md` Phase 4; DIR-01 ships in-tree built-ins only.
5. Multi-utterance windowing or rolling-context state. Each utterance is classified and enriched independently. Stateful chains are deferred.
6. Sharing a single loaded model file between `intel.py` and the dictation runtime. They MAY use different models concurrently; runtime memory budgeting across both is a DIR-02 question.

## 4. Relationship to Existing Plans

1. **Parent RFC:** `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` defines the `Plugin` protocol, `ContextEnvelope`, plugin kinds, and capability model. DIR-01 extends that taxonomy with a new `transducer` kind and reuses the host execution semantics.
2. **Sibling phase:** `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` (MIR-01) covers meeting-side multi-intent routing on rolling windows with deterministic lexical signals. DIR-01 is the live single-utterance counterpart with LLM-based classification. Implementations MUST share `holdspeak/plugins/contracts.py` types where they overlap.
3. **Project KB integration:** Project knowledge bases shipped in commit `0b05af6` and surfaced through `holdspeak/plugins/project_detector.py` are the lookup target for the `kb-enricher` stage. DIR-01 does not modify the KB schema; it only reads.

## 5. Entry Criteria

All MUST be true before implementation begins.

1. Baseline `uv run pytest` passes.
2. `holdspeak doctor` reports `Web runtime: PASS` and `Transcription backend: mlx` on the reference machine.
3. `llama-cpp-python>=0.2.90` is installed (Metal-enabled wheel on macOS arm64; standard wheel elsewhere) and a Qwen-family GGUF can be loaded outside the application.
4. Existing typing path benchmarks captured: median time from hotkey release to text injection over a 50-utterance fixture set, recorded in evidence as `00_baseline_typing_latency.txt`.
5. Disk space available for at least one 4-bit Qwen model (≤6 GB).

## 6. Architecture Delta

### 6.1 Pipeline Topology

Current path (controller.py:136-180):

```
audio → Transcriber.transcribe → TextProcessor.process → TextTyper.type_text
```

DIR-01 path (when enabled):

```
audio
  → Transcriber.transcribe
  → TextProcessor.process               # existing punctuation/substitution
  → DictationPipeline.run               # NEW: ordered stage chain
        ├── stage: intent-router        # LLM classification → IntentTag
        ├── stage: kb-enricher          # IntentTag + ProjectKB → enriched text
        └── stage: <user-defined>       # extension point
  → TextTyper.type_text
```

The pipeline is a **single in-process call**. Stages run synchronously in declared order. Failure of any stage MUST short-circuit to the original (post-`TextProcessor`) text and emit a structured warning. The pipeline is invoked iff `dictation.pipeline.enabled = true` in config.

### 6.2 New Modules

1. `holdspeak/plugins/dictation/__init__.py`
2. `holdspeak/plugins/dictation/pipeline.py` — ordered executor, error isolation, telemetry hooks.
3. `holdspeak/plugins/dictation/contracts.py` — `Utterance`, `IntentTag`, `Transducer` protocol, `StageResult`.
4. `holdspeak/plugins/dictation/runtime.py` — long-lived `LLMRuntime` service wrapping `llama-cpp-python`, sharing loader patterns with `holdspeak/intel.py` (warm-up, eviction, error surfacing).
5. `holdspeak/plugins/dictation/builtin/intent_router.py` — built-in classifier stage.
6. `holdspeak/plugins/dictation/builtin/kb_enricher.py` — built-in enrichment stage.
7. `holdspeak/plugins/dictation/blocks.py` — block-config loader, validation, project overrides.
8. `holdspeak/commands/dictation.py` — CLI entry: `holdspeak dictation dry-run "<text>"`, `holdspeak dictation blocks ls|show|validate`.

### 6.3 Modified Modules

1. `holdspeak/controller.py` — wire pipeline call between `text_processor.process` and `typer.type_text`. The wiring MUST be a no-op when the pipeline is disabled.
2. `holdspeak/config.py` — add `DictationPipelineConfig` (see §9.4).
3. `holdspeak/commands/doctor.py` — add LLM runtime + model-availability checks (see §9.5).
4. `holdspeak/web_server.py` — read-only API to introspect the latest pipeline run for the `/history` view; no live UI in DIR-01.

### 6.4 Contracts (extends `holdspeak/plugins/contracts.py`)

```python
@dataclass(frozen=True)
class Utterance:
    raw_text: str                   # post-TextProcessor text
    audio_duration_s: float
    transcribed_at: datetime
    project: ProjectContext | None  # from project_detector

@dataclass(frozen=True)
class IntentTag:
    matched: bool                   # router decided a block matched
    block_id: str | None
    confidence: float               # 0.0–1.0; 0 if not matched
    raw_label: str | None           # the model's literal label string
    extras: dict[str, Any]          # block-specific captures (e.g., stage="buildout")

@dataclass(frozen=True)
class StageResult:
    stage_id: str
    text: str                       # the (possibly transformed) text passed to next stage
    intent: IntentTag | None        # set by classifier stages, propagated forward
    elapsed_ms: float
    warnings: list[str]
    metadata: dict[str, Any]        # for introspection / debugging

class Transducer(Protocol):
    id: str
    version: str
    requires_llm: bool

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult: ...
```

`Transducer` is added as a new value of the existing `Plugin.kind` field (`"transducer"`). Existing kinds are unchanged.

## 7. On-Device LLM Runtime

### 7.1 Backend

`llama-cpp-python>=0.2.90`. The runtime MUST load the model once on first use and keep it resident. The runtime MUST be a singleton scoped to the controller process; no per-utterance reinstantiation. On macOS arm64 the Metal-enabled wheel is required (the project README already documents the `CMAKE_ARGS="-DGGML_METAL=on" uv pip install llama-cpp-python` pattern); on Linux x86_64 the standard wheel suffices, with optional CUDA-enabled builds documented but not required.

The runtime layer MUST be implemented so that the eventual addition of a Metal-native backend (MLX-LM) or a remote backend is a localized change in `runtime.py` and does not touch stage code. This is a structural requirement, not a delivery requirement.

### 7.2 Model Selection (Reference Defaults)

Per the user constraint "we need qwen", the candidate set is restricted to the Qwen family in GGUF format. Recommended sources are `bartowski/Qwen2.5-*-Instruct-GGUF` and `lmstudio-community/Qwen2.5-*-Instruct-GGUF` on HuggingFace. Quant choice favors `Q4_K_M` (good speed/quality tradeoff) over `Q4_0` (faster, lower quality) and `Q5_K_M` (slower, marginal gain) for routing tasks.

| Tier | Model | Use case | Latency target (warm, reference Mac) |
|---|---|---|---|
| Default | `Qwen2.5-3B-Instruct-Q4_K_M.gguf` | Routing + classification | first-token ≤ 250ms, ≥40 tok/s sustained |
| Fast | `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf` | Strict latency budgets | first-token ≤ 150ms |
| Quality | `Qwen2.5-7B-Instruct-Q4_K_M.gguf` | Fallback when 3B misclassifies | first-token ≤ 500ms |

Note the latency targets are slightly looser than an MLX-LM variant of this design would be (~30–50% slower at the same quant on Apple Silicon), but stay well inside the §9.6 budget for the 1.5B/3B tiers.

**Validation requirement:** §12.10 mandates a benchmark spike that measures all three tiers on the reference machine and records actual numbers. The default tier MAY be revised to a Qwen3 GGUF variant **only if** the benchmark demonstrates better latency *and* equal-or-better label accuracy on the fixture set. Until then, Qwen2.5-3B-Q4_K_M is the committed default.

### 7.3 Constrained Decoding

The intent router MUST emit a structured response conforming to a fixed JSON schema:

```json
{"matched": true, "block_id": "ai_prompt_buildout", "confidence": 0.87, "extras": {"stage": "buildout"}}
```

Free-form prose output is forbidden. DIR-01 commits to **GBNF grammar-constrained decoding** as built into `llama-cpp-python` via the `grammar=` argument on `Llama.create_completion` / `Llama.__call__`. Rationale:

1. Built into the chosen runtime — zero additional library dependency.
2. Deterministic and exhaustive: the model token sampler is restricted at decode time, not validated post-hoc, so malformed JSON is structurally impossible.
3. Block-id and extras-enum values are derived directly from the loaded `blocks.yaml`, so the grammar is data-driven and updates whenever block config changes.
4. Mature and well-tested; no library-churn risk.

The grammar generation is the responsibility of `holdspeak/plugins/dictation/grammars.py` (new module), which MUST produce a GBNF string for a given set of blocks and validate it via `LlamaGrammar.from_string` at config-load time.

JSON-mode + post-hoc retry is **explicitly rejected** as a fallback: with grammar-constrained decoding there is nothing to fall back to. If the grammar fails to compile, the dictation runtime MUST refuse to start and `holdspeak doctor` MUST surface the error.

### 7.4 Forward Compatibility

See §7.1 final paragraph. The runtime interface (`classify(prompt, schema) → dict`) is backend-agnostic. A future MLX-LM backend, if measured benchmarks justify the second runtime, would land as `runtime_mlx.py` selected by config — no stage-code changes. This is **not** a DIR-01 deliverable.

## 8. Block Configuration Schema

### 8.1 File Layout

Block configs live as YAML at:

1. **Global default:** `~/.config/holdspeak/blocks.yaml` (user scope)
2. **Per-project override:** `<project_root>/.holdspeak/blocks.yaml` (auto-discovered via `project_detector`)

If both exist, project-scope blocks fully replace global blocks for that project (no merge, to avoid surprise composition). A future `merge: true` flag MAY be added.

### 8.2 Schema

```yaml
version: 1
default_match_confidence: 0.6   # below this, treat as no match

blocks:
  - id: ai_prompt_buildout
    description: "User is building out a prompt for an AI assistant — buildout phase."
    match:
      # Examples shown to the model as positive cases.
      examples:
        - "Claude, I want you to build a new module that handles..."
        - "ChatGPT, please create a function that..."
      # Optional negative examples to disambiguate.
      negative_examples:
        - "What time is it?"
      # Required structured output keys with their allowed enum values.
      extras_schema:
        stage:
          type: enum
          values: [buildout, refinement, debugging, documentation]
    inject:
      mode: append   # append | prepend | replace
      template: |
        {raw_text}

        ---
        Project context (auto-injected by HoldSpeak):
        - Repo: {project.name} ({project.root})
        - Stack: {project.kb.stack}
        - Recent decisions: {project.kb.recent_adrs_short}
        - Current task focus: {project.kb.task_focus}

  - id: documentation_exercise
    description: "User is dictating documentation for code or a system."
    match:
      examples:
        - "This module is responsible for..."
        - "The endpoint accepts a JSON body with..."
    inject:
      mode: append
      template: |
        {raw_text}

        <!-- HoldSpeak: see {project.kb.docs_index} for related docs -->
```

### 8.3 Template Variables

Templates use `{}` placeholders resolved by the `kb-enricher` stage. The variable namespace MUST be:

1. `{raw_text}` — the post-TextProcessor utterance.
2. `{project.*}` — fields from the detected `ProjectContext`.
3. `{project.kb.*}` — keys from the project's knowledge base.
4. `{intent.extras.*}` — captures from the router's `extras` dict (e.g., `{intent.extras.stage}`).

Unresolved placeholders MUST cause the stage to skip injection and emit a warning, **never** to type the literal `{...}` into the destination app.

## 9. Detailed Requirements

### 9.1 Functional Requirements

- `DIR-F-001` Pipeline MUST execute stages in declared order.
- `DIR-F-002` Pipeline MUST be no-op when `dictation.pipeline.enabled = false`.
- `DIR-F-003` Any stage exception MUST short-circuit to the input text passed to the pipeline; the original utterance is always typeable.
- `DIR-F-004` Intent router MUST return a `IntentTag` with `matched=false` and `confidence=0.0` if the model output cannot be parsed after constrained-decoding retry.
- `DIR-F-005` Router MUST score against the union of all blocks loaded for the active project (or global, if no project).
- `DIR-F-006` `kb-enricher` MUST only act on `IntentTag.matched=true` with `confidence >= block.match.threshold` (or the global default).
- `DIR-F-007` `kb-enricher` MUST never type unresolved `{...}` placeholders.
- `DIR-F-008` Per-project blocks MUST fully replace global blocks for that project (no implicit merge).
- `DIR-F-009` Pipeline MUST capture per-stage `StageResult` for the most recent N utterances (default N=20) for introspection.
- `DIR-F-010` `holdspeak dictation dry-run "<text>"` MUST execute the full pipeline against a synthetic `Utterance` without invoking the keyboard typer and print each stage's `StageResult`.
- `DIR-F-011` Disabling the LLM runtime in config MUST cause `intent-router` to be skipped (not error) and downstream stages to receive `IntentTag.matched=false`.

### 9.2 Data Requirements

- `DIR-D-001` Block config schema MUST be versioned via top-level `version: 1`.
- `DIR-D-002` Loader MUST validate against the schema and produce actionable error messages on malformed YAML.
- `DIR-D-003` No DB schema changes are required for DIR-01. Recent-runs introspection (DIR-F-009) is in-memory only.

### 9.3 API and UX Requirements

- `DIR-A-001` CLI MUST expose: `dry-run`, `blocks ls`, `blocks show <id>`, `blocks validate`, `runtime status`.
- `DIR-A-002` Web `/history` MAY render the most recent pipeline run with per-stage details. Live web controls are NOT required for DIR-01.
- `DIR-A-003` `holdspeak doctor` MUST report LLM runtime status, model presence, and constrained-decoding library availability.

### 9.4 Configuration Requirements

Add to `Config`:

```python
@dataclass
class DictationPipelineConfig:
    enabled: bool = False              # OFF by default
    stages: list[str] = field(default_factory=lambda: ["intent-router", "kb-enricher"])
    max_total_latency_ms: int = 600    # hard ceiling; if exceeded, short-circuit next time

@dataclass
class LLMRuntimeConfig:
    backend: str = "llama-cpp"         # only value in DIR-01
    model_path: str = "~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf"
    n_ctx: int = 2048                  # ample for one utterance + grammar overhead
    n_threads: int | None = None       # None → llama-cpp default
    n_gpu_layers: int = -1             # -1 = all on GPU/Metal where available
    warm_on_start: bool = False        # if true, load model at controller init
    eviction_idle_seconds: int = 0     # 0 = never evict
```

- `DIR-C-001` Defaults MUST keep DIR-01 fully off for existing users.
- `DIR-C-002` Config validation MUST reject unknown stage IDs at load time.

### 9.5 Doctor Requirements

- `DIR-DOC-001` New check `LLM runtime` reports backend, model id, and load status (loaded | available | missing).
- `DIR-DOC-002` New check `Grammar compilation` reports whether the GBNF grammar generated from the loaded `blocks.yaml` compiles successfully via `LlamaGrammar.from_string`.
- `DIR-DOC-003` Both checks MUST be `INFO`/`WARN` (not `FAIL`) when DIR-01 is disabled — the pipeline is opt-in.

### 9.6 Reliability and Performance Requirements

- `DIR-R-001` Warm `intent-router` median latency MUST be ≤ 250ms on reference Mac (Qwen2.5-3B-Q4_K_M, Metal).
- `DIR-R-002` Warm `intent-router` p95 latency MUST be ≤ 500ms on reference Mac.
- `DIR-R-001-LX` On Linux x86_64 with no GPU, the intent router MAY take ≤ 800ms median; this is informational, not a phase gate.
- `DIR-R-003` Cold-start (first call after `holdspeak` launch with `warm_on_start=false`) MUST complete or short-circuit within `max_total_latency_ms` × 5; otherwise log and disable for the session.
- `DIR-R-004` `kb-enricher` MUST be pure template substitution; latency MUST be ≤ 5ms.
- `DIR-R-005` Total pipeline latency overhead vs baseline MUST be ≤ 250ms median, ≤ 500ms p95 on the reference machine.

### 9.7 Observability Requirements

- `DIR-O-001` Each pipeline run MUST emit a structured log line containing stage IDs, elapsed_ms per stage, intent tag, and warnings.
- `DIR-O-002` LLM runtime MUST emit counters: `model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`.
- `DIR-O-003` Logs MUST NOT contain raw block templates if those templates contain user-marked secrets (future); for DIR-01, document that templates are not redacted.

### 9.8 Security and Trust Requirements

- `DIR-S-001` Block configs are user-authored; the loader MUST treat them as trusted but MUST NOT execute arbitrary code (no `!!python/object` YAML tags — use safe loader).
- `DIR-S-002` Templates MUST NOT execute shell or Python; only `{key}` substitution is supported.
- `DIR-S-003` The LLM runtime MUST NOT make network calls. Model files come from the HuggingFace cache only; remote fetch is the user's responsibility.

## 10. Verification Strategy

### 10.1 Methods

`UT` unit, `IT` integration, `AT` API/CLI, `BT` benchmark, `MT` manual trace, `LG` log/metrics.

### 10.2 Requirement-to-Verification Matrix

| Requirement | Method | Verification Demand | Evidence |
|---|---|---|---|
| DIR-F-001 | UT | Stages execute in declared order with mocked transducers | `10_ut_pipeline.log` |
| DIR-F-002 | UT | Pipeline disabled → no stage invoked | `10_ut_pipeline.log` |
| DIR-F-003 | UT | Stage raising → original text returned, warning emitted | `10_ut_pipeline.log` |
| DIR-F-004 | UT | Garbled model output → matched=false after retry | `10_ut_router.log` |
| DIR-F-005 | UT | Multiple blocks loaded → router scores against union | `10_ut_router.log` |
| DIR-F-006 | UT | Below-threshold confidence → enricher no-op | `10_ut_enricher.log` |
| DIR-F-007 | UT | Missing template var → no injection, warning | `10_ut_enricher.log` |
| DIR-F-008 | UT | Project blocks fully replace global | `10_ut_blocks.log` |
| DIR-F-009 | UT | Last-N introspection ring buffer | `10_ut_pipeline.log` |
| DIR-F-010 | AT | `dictation dry-run` prints stage results | `40_cli_checks.log` |
| DIR-F-011 | UT | LLM disabled → router skipped, downstream sees matched=false | `10_ut_runtime.log` |
| DIR-D-001 | UT | Schema version validation | `10_ut_blocks.log` |
| DIR-D-002 | UT | Malformed YAML produces actionable error | `10_ut_blocks.log` |
| DIR-A-001 | AT | All CLI subcommands return zero on happy path | `40_cli_checks.log` |
| DIR-A-003 | AT | Doctor includes new checks with correct statuses | `41_doctor_checks.log` |
| DIR-C-001 | UT | Default config: pipeline disabled | `10_ut_config.log` |
| DIR-C-002 | UT | Unknown stage id rejected | `10_ut_config.log` |
| DIR-DOC-001..003 | AT | Doctor output text contains required check names | `41_doctor_checks.log` |
| DIR-R-001..R-005 | BT | Benchmark harness on reference machine | `50_perf.txt` |
| DIR-O-001..O-002 | LG | Log line and counter inspection | `60_logs_sample.txt` |
| DIR-S-001 | UT | YAML loader rejects unsafe tags | `10_ut_security.log` |
| DIR-S-002 | UT | Template substitution rejects expressions | `10_ut_security.log` |
| DIR-S-003 | MT | Network calls absent from runtime trace | `61_runtime_trace.txt` |

## 11. Evidence Bundle

### 11.1 Required Folder

`docs/evidence/phase-dir-01/<YYYYMMDD-HHMM>/`

### 11.2 Required Files

`00_baseline_typing_latency.txt`, `00_manifest.md`, `01_env.txt`, `02_git_status.txt`, `03_traceability.md`, `10_ut_pipeline.log`, `10_ut_router.log`, `10_ut_enricher.log`, `10_ut_blocks.log`, `10_ut_runtime.log`, `10_ut_config.log`, `10_ut_security.log`, `12_grammar_validation.log`, `40_cli_checks.log`, `41_doctor_checks.log`, `50_perf.txt`, `51_model_tier_benchmark.md`, `60_logs_sample.txt`, `61_runtime_trace.txt`, `99_phase_summary.md`.

### 11.3 Validity Rules

Identical to `PLAN_PHASE_MULTI_INTENT_ROUTING.md` §8.3 (commands, timestamps, commit hashes, no deletion of failures).

## 12. Implementation Recipe

### 12.1 Step 0 — Baseline + Spike

1. Capture baseline typing latency (50-utterance fixture) → `00_baseline_typing_latency.txt`.
2. Confirm `llama-cpp-python` Metal wheel is installed (reuse the existing `[meeting]` extra path; document the `CMAKE_ARGS="-DGGML_METAL=on"` install if rebuild needed).
3. Spike: load `Qwen2.5-3B-Instruct-Q4_K_M.gguf`, run a 10-prompt classification fixture with a fixed GBNF grammar, measure first-token + total. Record raw → `51_model_tier_benchmark.md` (initial entry).

### 12.2 Step 1 — Contracts

1. Add `holdspeak/plugins/dictation/contracts.py` with `Utterance`, `IntentTag`, `StageResult`, `Transducer`.
2. Extend `holdspeak/plugins/contracts.py` to allow `kind="transducer"`.
3. Unit tests: `tests/unit/test_dictation_contracts.py`.

### 12.3 Step 2 — Pipeline Executor

1. Implement `pipeline.py` with ordered execution, error isolation, ring buffer.
2. Unit tests: `tests/unit/test_dictation_pipeline.py`.

### 12.4 Step 3 — LLM Runtime

1. Implement `runtime.py` wrapping `llama-cpp-python` (`Llama` instance, warm/lazy modes, `classify(prompt, grammar) → dict`). Reuse the loader-failure handling pattern from `holdspeak/intel.py`.
2. Implement `grammars.py` to generate a GBNF grammar from a loaded `BlockSet` and validate it via `LlamaGrammar.from_string` at construction.
3. Unit tests with a mocked `Llama`; integration tests gated on a `requires_llama_cpp` marker (skipped if the runtime can't load the configured model).

### 12.5 Step 4 — Blocks

1. Implement `blocks.py`: YAML loader (safe), schema validation, project override resolution.
2. Ship example `blocks.yaml` under `holdspeak/static/examples/blocks.example.yaml`.
3. Unit tests: `tests/unit/test_blocks.py`.

### 12.6 Step 5 — Built-in Stages

1. Implement `intent_router.py` and `kb_enricher.py`.
2. Unit tests with mocked runtime + fixed block config.

### 12.7 Step 6 — Controller Wiring

1. Wire `DictationPipeline` between `text_processor.process` and `typer.type_text` in `controller.py:140-148`.
2. Guard with `dictation.pipeline.enabled`.
3. Integration test: synthetic audio fixture → end-to-end (mocked typer).

### 12.8 Step 7 — CLI

1. Implement `holdspeak/commands/dictation.py` and register in `main.py`.
2. CLI tests: `tests/integration/test_dictation_cli.py`.

### 12.9 Step 8 — Doctor

1. Add LLM runtime + constrained-decoding checks per §9.5.
2. Update `tests/unit/test_doctor_command.py`.

### 12.10 Step 9 — Benchmarks

1. Implement `scripts/bench_dictation_pipeline.py` running the fixture against all three Qwen tiers.
2. Run on reference machine; record numbers → `50_perf.txt`, `51_model_tier_benchmark.md`.
3. **Decision gate:** if Qwen2.5-3B does not meet DIR-R-001/R-002, escalate per §13.

### 12.11 Step 10 — Full Regression

```bash
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run python -m compileall holdspeak
```

## 13. Risks and Mitigations

1. **LLM latency exceeds budget on weaker M-chips.** Mitigation: ship Qwen2.5-1.5B-Q4_K_M as fallback default if 3B fails on baseline reference machine; document the floor (e.g., M1 8GB).
2. **`llama-cpp-python` wheel mismatch (no Metal).** A pip-installed wheel without Metal flags will run CPU-only on Apple Silicon and miss latency targets dramatically. Mitigation: doctor check inspects whether the loaded `Llama` reports GPU offload >0; surface a clear remediation hint pointing to the `CMAKE_ARGS="-DGGML_METAL=on"` rebuild command (which the project README already documents for the meeting-intel path).
3. **Concurrent memory pressure with `intel.py`.** If the user runs meeting-intel and the dictation router simultaneously, two GGUF models compete for RAM. Mitigation: §3.2 item 6 marks shared-model-instance as out of scope; DIR-01 documents the conservative defaults and leaves coexistence as a DIR-02 question.
4. **Project KB key drift.** Templates reference `{project.kb.*}` keys that may not exist in older KBs. Mitigation: DIR-F-007 + actionable warning + `dictation blocks validate --project` CLI.
5. **User confusion when enrichment silently no-ops.** Mitigation: ring-buffer introspection (DIR-F-009) + dry-run CLI (DIR-F-010) make every decision auditable.
6. **Mid-utterance context bleed across utterances.** Out of scope — DIR-01 is stateless. Documented as a non-goal in §3.2.
7. **Model file size + first-launch surprise.** A Q4_K_M 3B Qwen GGUF is ~2 GB. Mitigation: doctor emits the warning; pipeline stays disabled by default; never auto-download in DIR-01.
8. **GBNF grammar bug from malformed `blocks.yaml`.** Mitigation: grammar compilation is checked at config-load time (DIR-DOC-002) and at `dictation blocks validate`; pipeline refuses to start with a broken grammar.

## 14. Definition of Done

1. Every `DIR-*` requirement has passing verification evidence.
2. Required evidence files exist and are non-empty.
3. Pipeline runs end-to-end on the reference machine with default-Qwen2.5-3B and meets DIR-R-001/R-002.
4. With `dictation.pipeline.enabled=false`, all baseline behavior is byte-identical to pre-DIR-01.
5. `holdspeak doctor` cleanly reports the new checks in both enabled and disabled states.
6. `51_model_tier_benchmark.md` contains measured numbers for all three Qwen tiers; the chosen default is justified by those numbers.
7. Phase summary lists known gaps and explicitly defers DIR-02 items (cross-platform backend, cloud router, multi-utterance state).

## 15. Open Questions (Resolve Before Step 5)

1. ~~**Outlines vs json-mode.**~~ Resolved: DIR-01 uses GBNF grammar via `llama-cpp-python` (§7.3).
2. **Qwen2.5 vs Qwen3.** Should the default be re-evaluated against a Qwen3-3B-class GGUF if one with stable accuracy exists at phase start? Resolved by §12.10 benchmark.
3. **Template engine.** Plain `str.format` vs Jinja2 (sandboxed). DIR-01 commits to plain `str.format` for security simplicity (§9.8). Revisit only if real users hit expressivity limits.
4. **Where do block-config edits live in the web UI?** Out of scope for DIR-01; CLI and file editing only. Web editor is a DIR-02 candidate.
5. **Should the router emit multi-label outputs?** No, DIR-01 commits to single-block-match for simplicity. Multi-label is a DIR-02 candidate, aligned with MIR-01's multi-label patterns.
6. **Model coexistence with `intel.py`.** Two simultaneously loaded GGUFs is unconstrained in DIR-01. A DIR-02 spike should evaluate (a) sharing one model across both runtimes and (b) a process-level memory budget.
