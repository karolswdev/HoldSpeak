# Phase 1 — Dictation Intent Routing (DIR-01)

**Last updated:** 2026-04-25.

## Goal

Deliver DIR-01 per `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`: a
real-time, on-device transcript enrichment pipeline for the voice-typing
path. The pipeline runs an LLM-driven intent router (Qwen GGUF on
`llama-cpp-python`, GBNF-constrained) followed by a KB-driven enrichment
stage between Whisper and the keyboard. Off by default; opt-in per user
config. This section is **immutable** for the life of the phase.

## Scope

- **In:** Everything declared in scope by `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §3.1. Implemented via stories `HS-1-01` through `HS-1-11` (one per spec §12 step). Phase exit is gated by the spec's §14 "Definition of Done".
- **Out:** Everything declared out-of-scope by `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §3.2 — notably MLX-LM as a second on-device backend, cloud router fallback, web block editor, multi-utterance state, and shared model file with `intel.py`.

## Exit criteria (evidence required)

- [ ] All §9 `DIR-*` requirements have passing verification per the matrix in §10.2.
- [ ] Evidence bundle at `docs/evidence/phase-dir-01/<YYYYMMDD-HHMM>/` contains every file listed in spec §11.2.
- [ ] `dictation.pipeline.enabled = true` end-to-end run on the reference Mac with default Qwen2.5-3B-Q4_K_M meets DIR-R-001 (≤250ms median) and DIR-R-002 (≤500ms p95).
- [ ] With `dictation.pipeline.enabled = false`, baseline typing behavior is byte-identical to pre-DIR-01.
- [ ] `holdspeak doctor` cleanly reports new checks (`LLM runtime`, `Grammar compilation`) in both enabled and disabled states.
- [ ] `51_model_tier_benchmark.md` records measured numbers for all three Qwen tiers; chosen default is justified by those numbers.
- [ ] Phase summary lists known gaps and explicitly defers DIR-02 items.

## Story status

Mapping: each story corresponds to one spec §12 step. Stories are
created ahead of time as `backlog` so the work is visible; only the
"in-progress" story has a fully fleshed-out file at any given time.

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-1-01 | Step 0 — Baseline + llama-cpp/Qwen spike | ready | [story-01-baseline-and-spike](./story-01-baseline-and-spike.md) | (pending) |
| HS-1-02 | Step 1 — Transducer contracts | ready | [story-02-contracts](./story-02-contracts.md) | (pending) |
| HS-1-03 | Step 2 — Pipeline executor | backlog | (pending) | — |
| HS-1-04 | Step 3 — LLM runtime + GBNF grammars | backlog | (pending) | — |
| HS-1-05 | Step 4 — Block config loader | backlog | (pending) | — |
| HS-1-06 | Step 5 — Built-in stages (intent-router + kb-enricher) | backlog | (pending) | — |
| HS-1-07 | Step 6 — Controller wiring | backlog | (pending) | — |
| HS-1-08 | Step 7 — CLI (`holdspeak dictation …`) | backlog | (pending) | — |
| HS-1-09 | Step 8 — Doctor checks (LLM runtime + grammar compilation) | backlog | (pending) | — |
| HS-1-10 | Step 9 — Benchmarks across Qwen tiers | backlog | (pending) | — |
| HS-1-11 | Step 10 — Full regression + DoD | backlog | (pending) | — |

## Where we are

Phase opening. Spec is locked. `HS-1-01` is the next thing to ship: a
baseline-typing-latency measurement, a `llama-cpp-python`/Metal
Qwen2.5-3B-Q4_K_M install verification, and a 10-prompt classification
spike with a fixed GBNF grammar. The result of HS-1-01 either confirms
or invalidates the §7.2 latency targets before any pipeline code is
written.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `llama-cpp-python` Metal wheel not installed → CPU-only inference, latency targets fail | medium | Doctor check inspects GPU offload; HS-1-01 spike measures and surfaces immediately | Spike measurement shows >2× the §7.2 target latency |
| Qwen2.5-3B-Q4_K_M misclassifies the fixture → forces escalation to 7B | medium | HS-1-10 benchmarks the full tier set; default can be revised to 1.5B (faster) or 7B (more accurate) per measurement | Spike accuracy <70% on the 10-prompt fixture |
| GBNF grammar from `blocks.yaml` fails to compile | low | DIR-DOC-002 doctor check + config-load-time validation in `grammars.py` | Any `LlamaGrammar.from_string` exception in CI |
| Pipeline overhead pushes hotkey-release-to-typing latency past the perception threshold (~400ms total) | medium | DIR-R-005 caps overhead at ≤250ms median; if breached, default tier drops to 1.5B | DIR-R-001 evidence shows median >250ms after warm-up |
| Two GGUF models (intel + dictation) loaded concurrently OOM the user's machine | medium | §3.2 item 6 marks shared-instance out of scope; conservative defaults; documented in risks | First user report of OOM |

## Decisions made (this phase)

- 2026-04-25 — Backend is `llama-cpp-python` (Metal on Mac, CPU/CUDA on Linux). MLX-LM rejected for DIR-01 — would mean two on-device LLM stacks alongside `intel.py` — owner: agent + user (user pushback that we should reuse the existing runtime).
- 2026-04-25 — Constrained decoding via GBNF grammar (built into `llama-cpp-python`). `outlines` rejected — extra dep, library churn risk, no benefit over GBNF — owner: agent.
- 2026-04-25 — Default model `Qwen2.5-3B-Instruct-Q4_K_M.gguf` (sources: `bartowski/`, `lmstudio-community/`). Tiers: 1.5B (fast), 3B (default), 7B (quality fallback). Qwen3 only after a benchmark beats Qwen2.5 — owner: agent + user (user said "we need qwen").
- 2026-04-25 — Pipeline off by default (`dictation.pipeline.enabled = false`). Opt-in via config — owner: agent.

## Decisions deferred

- MLX-LM as a second backend — trigger: a real user benchmark on Apple Silicon shows the 30–50% latency advantage matters for their flow — default: never adopt.
- Cloud LLM router fallback — trigger: enough users want zero-local-model setup — default: never (HoldSpeak is local-first).
- Web-based block editor — trigger: ≥3 user reports that file editing is the friction — default: CLI + file editing only.
