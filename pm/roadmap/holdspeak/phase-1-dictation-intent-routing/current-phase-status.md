# Phase 1 — Dictation Intent Routing (DIR-01)

**Last updated:** 2026-04-25 (HS-1-05 block-config loader shipped).

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
| HS-1-06 | Step 5 — Built-in stages (intent-router + kb-enricher) | backlog | (pending) | — |
| HS-1-07 | Step 6 — Controller wiring | backlog | (pending) | — |
| HS-1-08 | Step 7 — CLI (`holdspeak dictation …`) | backlog | (pending) | — |
| HS-1-09 | Step 8 — Doctor checks (LLM runtime + structured-output compile) | backlog | (pending) | — |
| ~~HS-1-10~~ | ~~Step 9 — Benchmarks~~ | dropped | — | n/a — no pre-shipping measurement gate per 2026-04-25 amendment |
| HS-1-11 | Step 10 — Full regression + DoD | backlog | (pending) | — |

## Where we are

Spec amended (2026-04-25) to ship two backends (`mlx-lm` +
`llama-cpp-python`) behind a pluggable `LLMRuntime` Protocol with
`Qwen3-8B-MLX-4bit` as the reference-Mac primary. All pre-shipping
measurement is dropped — DIR-01 banks on the chosen models and goes
straight to implementation. `HS-1-01` (baseline) and `HS-1-10`
(benchmarks) are dropped.

**HS-1-05 done.** `holdspeak/plugins/dictation/blocks.py` ships the
typed loader for the §8 block-config YAML: `Block`, `MatchSpec`,
`InjectSpec`, `LoadedBlocks` (frozen), `InjectMode` enum, and
`load_blocks_yaml` / `resolve_blocks` / `validate_template`.
`yaml.safe_load` covers DIR-S-001 (rejects `!!python/object/...`
tags); `validate_template` enforces DIR-S-002 by accepting only
dotted-name placeholders (`{a.b.c}`) and rejecting format specs,
conversions, method calls, item access, and arithmetic.
`resolve_blocks` implements §8.1 / DIR-F-008 — project-scope blocks
fully replace global. `LoadedBlocks.to_block_set()` bridges to the
HS-1-04 constraint compiler. `PyYAML>=6.0` is now an explicit core
dep. 24-case unit suite passes; full regression: 848 passed, 1
pre-existing hardware-only `tests/e2e/test_metal.py` fail (Whisper
model load), unrelated. Next: **HS-1-06** (built-in `intent-router`
+ `kb-enricher` stages).

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
