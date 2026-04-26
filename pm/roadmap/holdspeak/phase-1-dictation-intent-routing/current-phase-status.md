# Phase 1 — Dictation Intent Routing (DIR-01)

**Last updated:** 2026-04-25 (HS-1-09 doctor checks shipped — `LLM runtime` + `Structured-output compilation`).

## Goal

Deliver DIR-01 per `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`: a
real-time, on-device transcript enrichment pipeline for the voice-typing
path. The pipeline runs an LLM-driven intent router behind a pluggable
`LLMRuntime` Protocol — DIR-01 ships two concrete backends (`mlx-lm`
with `Qwen3-8B-MLX-4bit` as the reference-Mac primary, and
`llama-cpp-python` with `Qwen2.5-3B-Q4_K_M` as the cross-platform
default), with constrained-decoding behind a shared schema compiler
(GBNF on `llama_cpp`, `outlines`-style on `mlx`). A KB-driven enrichment
stage follows. Off by default; opt-in per user config. This section is
**immutable** for the life of the phase.

## Scope

- **In:** Everything declared in scope by `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §3.1. Implemented via stories `HS-1-02` through `HS-1-09` and `HS-1-11` (HS-1-01 and HS-1-10 dropped per the 2026-04-25 amendment). Phase exit is gated by the spec's §14 "Definition of Done".
- **Out:** Everything declared out-of-scope by `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §3.2 — notably MLX-LM as a second on-device backend, cloud router fallback, web block editor, multi-utterance state, and shared model file with `intel.py`.

## Exit criteria (evidence required)

- [ ] All §9 `DIR-*` requirements have passing verification per the matrix in §10.2.
- [ ] Evidence bundle at `docs/evidence/phase-dir-01/<YYYYMMDD-HHMM>/` contains every file listed in spec §11.2.
- [ ] `dictation.pipeline.enabled = true` end-to-end run on the reference Mac with the `mlx` Qwen3-8B-MLX-4bit primary works and feels responsive in real use. The `llama_cpp` Qwen2.5-3B-Q4_K_M path also runs end-to-end.
- [ ] With `dictation.pipeline.enabled = false`, typing behavior is byte-identical to pre-DIR-01.
- [ ] `holdspeak doctor` cleanly reports new checks (`LLM runtime`, `Structured-output compilation`) in both enabled and disabled states, for the active backend.
- [ ] Phase summary lists known gaps and explicitly defers DIR-02 items.

## Story status

Mapping: each story corresponds to one spec §12 step. Stories are
created ahead of time as `backlog` so the work is visible; only the
"in-progress" story has a fully fleshed-out file at any given time.

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| ~~HS-1-01~~ | ~~Step 0 — Baseline / spike~~ | dropped | — | n/a — no pre-shipping measurement gate per 2026-04-25 amendment |
| HS-1-02 | Step 1 — Transducer contracts | done | [story-02-contracts](./story-02-contracts.md) | tests pass (5/5) + full suite green (excl. pre-existing metal hw fails) |
| HS-1-03 | Step 2 — Pipeline executor | done | [story-03-pipeline](./story-03-pipeline.md) | tests pass (11/11) + full suite green (excl. one pre-existing metal hw fail) |
| HS-1-04 | Step 3 — Pluggable LLM runtime (mlx + llama_cpp) + structured output | done | [story-04-runtime](./story-04-runtime.md) | tests pass (29 unit cases + 2 model-gated integration harnesses skip cleanly) |
| HS-1-05 | Step 4 — Block config loader | done | [story-05-blocks](./story-05-blocks.md) | tests pass (24 unit cases) |
| HS-1-06 | Step 5 — Built-in stages (intent-router + kb-enricher) | done | [story-06-builtin-stages](./story-06-builtin-stages.md) | tests pass (29 unit cases) |
| HS-1-07 | Step 6 — Controller wiring | done | [story-07-controller](./story-07-controller.md) | tests pass (5 new controller cases) + full suite green (excl. pre-existing metal hw fail) |
| HS-1-08 | Step 7 — CLI (`holdspeak dictation …`) | done | [story-08-cli](./story-08-cli.md) | tests pass (13 new CLI cases) + full suite green (excl. pre-existing metal hw fail) |
| HS-1-09 | Step 8 — Doctor checks (LLM runtime + structured-output compile) | done | [story-09-doctor](./story-09-doctor.md) | tests pass (8 new doctor cases) + full suite green (excl. pre-existing metal hw fail) |
| ~~HS-1-10~~ | ~~Step 9 — Benchmarks~~ | dropped | — | n/a — no pre-shipping measurement gate per 2026-04-25 amendment |
| HS-1-11 | Step 10 — Full regression + DoD | backlog | (pending) | — |

## Where we are

Spec amended (2026-04-25) to ship two backends (`mlx-lm` +
`llama-cpp-python`) behind a pluggable `LLMRuntime` Protocol with
`Qwen3-8B-MLX-4bit` as the reference-Mac primary. All pre-shipping
measurement is dropped — DIR-01 banks on the chosen models and goes
straight to implementation. `HS-1-01` (baseline) and `HS-1-10`
(benchmarks) are dropped.

**HS-1-09 done.** Two new doctor checks landed in
`holdspeak/commands/doctor.py`:
- `LLM runtime` (DIR-DOC-001) — reports requested + resolved
  backend (`mlx` | `llama_cpp`), resolution reason (so `auto` paths
  are visible), and configured model availability via
  `Path.exists()` (no cold-load on every doctor run). `WARN` with a
  `holdspeak[dictation-*]` install hint when the backend can't
  resolve, or with a "download model to PATH" hint when the file is
  missing.
- `Structured-output compilation` (DIR-DOC-002) — loads the global
  `blocks.yaml` via `resolve_blocks`, projects to a `BlockSet`, and
  runs the active backend's compiler (`to_outlines` for `mlx`,
  `to_gbnf` for `llama_cpp`). Pure-Python compile is cheap, so the
  doctor runs it eagerly. `WARN` on any compile-side exception with
  a "run `holdspeak dictation blocks validate`" hint.

Both checks honor DIR-DOC-003 — never `FAIL` (the existing
`PASS|WARN|FAIL` enum collapses spec "INFO" onto `PASS` per the
existing doctor convention; a clean install with
`pipeline.enabled = false` produces two informational `PASS` lines,
not noise). 8 new unit cases in `tests/unit/test_doctor_command.py`;
full regression: 903 passed, 13 skipped, 1 pre-existing
hardware-only `tests/e2e/test_metal.py` fail. Next: **HS-1-11** (DoD
sweep — every `DIR-*` requirement verified, evidence bundle, phase
summary).

---

**HS-1-08 done.** `holdspeak dictation` CLI surface landed:
`dry-run "<text>"` (DIR-F-010) prints stage-by-stage report, falls
back to `llm_enabled=False` (with a clear warning) when the runtime
backend can't load so block authors can validate YAML without
`mlx-lm` or `llama-cpp-python` installed; `blocks ls / show <id> /
validate [--project PATH]` (DIR-A-001); `runtime status` reports
the resolved backend + model availability without ever exiting
non-zero (it's a discovery surface — the doctor check is HS-1-09's
job). Pipeline assembly was lifted into
`holdspeak/plugins/dictation/assembly.py` with a `BuildResult`
return value; the controller's `_build_dictation_pipeline` now
delegates to it (single source of truth — the CLI and controller
can't drift). 13 new unit cases in `tests/unit/test_dictation_cli.py`;
full regression: 895 passed, 13 skipped, 1 pre-existing
hardware-only `tests/e2e/test_metal.py` fail (unrelated). Next:
**HS-1-09** (doctor checks: `LLM runtime` + `Structured-output
compilation`).

---

**HS-1-07 done.** Controller wiring landed in
`holdspeak/controller.py`. The dictation pipeline is invoked between
`text_processor.process` and `typer.type_text`, gated by
`dictation.pipeline.enabled` (DIR-C-001 — default `False`). All
`holdspeak.plugins.dictation.*` imports are confined to the lazy
`_build_dictation_pipeline` method, so the disabled path never
touches the dictation modules and stays byte-identical to pre-DIR-01
typing behavior (phase exit criterion #4). When enabled, the
controller resolves blocks via `resolve_blocks(global, None)`,
builds the runtime via `runtime.build_runtime(...)`, instantiates
`IntentRouter` + `KbEnricher` once per controller, and runs them
through `DictationPipeline` with a controller-side `on_run`
callback that emits the DIR-O-001 structured log line (stage IDs,
per-stage `elapsed_ms`, intent block_id, warnings,
`total_elapsed_ms`). Build failures are sticky for the controller
lifetime (no retry storms on a missing model file); `Utterance.run`
exceptions fall back to the original processed text — defense in
depth on top of the executor's per-stage error isolation
(DIR-F-003). `apply_runtime_config()` invalidates the cached
pipeline so toggling `dictation.*` config takes effect on the next
utterance. `Utterance.project = None` for now; `kb-enricher`'s
DIR-F-007 placeholder skip already handles missing `{project.*}`
context. Five new unit cases in `tests/unit/test_controller.py`;
full regression: 882 passed, 13 skipped, 1 pre-existing
hardware-only `tests/e2e/test_metal.py` fail (Whisper model load),
unrelated. Next: **HS-1-08** (CLI `holdspeak dictation …`).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `llama-cpp-python` Metal wheel not installed → CPU-only inference when `llama_cpp` backend is active | medium | Doctor check inspects GPU offload; remediation hint surfaces immediately | First user report of slow `llama_cpp` path |
| `mlx-lm` import failure on `auto` resolution silently falls back to `llama_cpp` and surprises the user | low | `auto` resolution path reported by `DIR-DOC-001`; explicit backend choice never falls back | Any user reports unexpected backend |
| Qwen3-8B-MLX-4bit RAM footprint (~5 GB resident) + `intel.py` Mistral-7B (~6 GB) OOM a 16 GB machine | medium | §3.2 #5 (no shared instance); doctor warns when both runtimes are warm-on-start on <16 GB | First user report of OOM |
| Constraint compile failure (GBNF or `outlines`) from a malformed `blocks.yaml` | low | DIR-DOC-002 + config-load-time validation in `grammars.py` for the active backend | Any compile exception in CI |
| Pipeline feels sluggish in real use on the `mlx` primary | medium | No numeric gate; if surfaced, default falls back to `llama_cpp` Qwen2.5-3B and the decision log is amended at that time | First user report of perception lag |
| Dual stack (`mlx-lm` + `llama-cpp-python`) bloats install / cold-start | low | Extras-gated install (`[dictation-mlx]`, `[dictation-llama]`); doctor reports which extras are present | Install size complaints in user feedback |

## Decisions made (this phase)

- 2026-04-25 — Pipeline off by default (`dictation.pipeline.enabled = false`). Opt-in via config — owner: agent.
- 2026-04-25 — **Pluggable LLM runtime: DIR-01 ships two backends.** `mlx-lm` (Apple Silicon native) and `llama-cpp-python` (cross-platform GGUF) behind a single `LLMRuntime` Protocol; selected by `dictation.runtime.backend: auto | mlx | llama_cpp` (default `auto`). **Supersedes the prior single-backend decision** — owner: agent + user (user: "abstracting away the execution interface ... implementing both").
- 2026-04-25 — **`mlx` primary model: `Qwen3-8B-MLX-4bit`** (`Qwen/Qwen3-8B-MLX-4bit`). Reference-Mac default. **Supersedes the prior "Qwen2.5-only" decision** — owner: user.
- 2026-04-25 — `llama_cpp` default model retained: `Qwen2.5-3B-Instruct-Q4_K_M.gguf` (`bartowski/Qwen2.5-3B-Instruct-GGUF`). Tiers: 1.5B / 3B / 7B — owner: agent.
- 2026-04-25 — Constrained decoding split per backend: GBNF for `llama_cpp`, `outlines`-style logits-processor for `mlx`. Both compiled from the same `BlockSet` by `grammars.py`. **Supersedes the prior "GBNF-only, outlines rejected" decision** — owner: agent + user (`outlines` accepted as a localized dep on the `mlx` path; churn risk contained to `runtime_mlx.py`).
- 2026-04-25 — **No pre-shipping measurement.** All baseline benches, validation spikes, and pre-ship benchmark gates are removed from DIR-01. The phase banks on `Qwen3-8B-MLX-4bit` (and the `llama_cpp` Qwen2.5-3B fallback) and ships on perception alone. **Drops HS-1-01 and HS-1-10.** **Supersedes the prior "validation via abstraction + HS-1-10 measurement" decision** — owner: user (explicit instruction: "I don't need a freakin' bench, we bank on qwen3-8b-mlx-4bit").

## Decisions deferred

- Cloud LLM router fallback — trigger: enough users want zero-local-model setup — default: never (HoldSpeak is local-first).
- Additional on-device backends beyond `mlx` and `llama_cpp` (vLLM, ollama, etc.) — trigger: measured advantage on the reference fixture — default: never.
- Web-based block editor — trigger: ≥3 user reports that file editing is the friction — default: CLI + file editing only.
- Shared model instance between `intel.py` and the dictation runtime — trigger: real OOM reports on common hardware — default: keep separate.
