# HS-1-04 — Step 3: Pluggable LLM runtime (mlx + llama_cpp) + structured output

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-02 (contracts), HS-1-03 (pipeline executor)
- **Unblocks:** HS-1-05 (block config loader), HS-1-06 (built-in stages), HS-1-09 (doctor checks)
- **Owner:** unassigned

## Problem

DIR-01 commits to an LLM-driven intent router (spec §7) but, per the
2026-04-25 amendment, ships **two** concrete on-device backends behind a
single `LLMRuntime` Protocol:

- `mlx` — `mlx-lm` with `Qwen3-8B-MLX-4bit` on Apple Silicon (primary on
  the reference Mac).
- `llama_cpp` — `llama-cpp-python` with `Qwen2.5-3B-Instruct-Q4_K_M.gguf`
  (cross-platform default; reuses the loader pattern from
  `holdspeak/intel.py`).

Stage code MUST NOT import either backend directly. Both runtimes serve
the same `classify(prompt, schema) -> dict` call and produce
constrained, structurally-valid JSON conforming to a backend-neutral
`StructuredOutputSchema`. Each backend compiles the schema to its
native mechanism (GBNF on `llama_cpp`, `outlines`-style logits processor
on `mlx`).

Per spec §7.1, backend selection is `dictation.runtime.backend: auto |
mlx | llama_cpp` (default `auto`). `auto` resolves to `mlx` on
`darwin/arm64` when `mlx-lm` is importable, else `llama_cpp`. Explicit
values never fall back; if the chosen backend is unavailable the
dictation runtime refuses to start and `holdspeak doctor` surfaces the
reason.

## Scope

- **In:**
  - `holdspeak/plugins/dictation/runtime.py` — `LLMRuntime` Protocol,
    `StructuredOutputSchema` dataclass, `auto`-resolution + factory,
    backend registry. No backend imports at module level — both are
    imported lazily by the factory.
  - `holdspeak/plugins/dictation/runtime_llama_cpp.py` — concrete
    `LlamaCppRuntime`. Wraps `Llama` with warm/lazy modes, reuses the
    loader-failure handling pattern from `holdspeak/intel.py`. Calls
    `Llama.create_completion(grammar=...)` for constrained decoding.
  - `holdspeak/plugins/dictation/runtime_mlx.py` — concrete `MlxRuntime`.
    Wraps `mlx_lm.load` + an `outlines`-style logits processor for
    structured-output sampling. Same `classify()` surface.
  - `holdspeak/plugins/dictation/grammars.py` — schema compiler with two
    emitters:
      - `to_gbnf(schema) -> str` (validated via `LlamaGrammar.from_string`).
      - `to_outlines(schema) -> Any` (validated at compile time).
    Both compile from the same `BlockSet`. Cross-backend equivalence is
    a unit test target: same `BlockSet` → outputs from the same value
    set regardless of which runtime produced them.
  - `LLMRuntimeConfig` extension in `holdspeak/config.py` per spec §9.4
    (backend, mlx_model, llama_cpp_model_path, n_ctx, n_threads,
    n_gpu_layers, warm_on_start, eviction_idle_seconds).
  - Unit tests with mocked backends (`tests/unit/test_dictation_runtime.py`,
    `tests/unit/test_dictation_grammars.py`). Integration tests gated on
    `requires_mlx` and `requires_llama_cpp` markers, skipped when the
    corresponding model isn't loadable.
- **Out:**
  - Doctor wiring (HS-1-09).
  - Block-config YAML loader (HS-1-05) — this story takes a hand-built
    `BlockSet` for tests.
  - Built-in `intent-router` / `kb-enricher` stages (HS-1-06).
  - Controller wiring (HS-1-07).
  - `pyproject.toml` extras for `[dictation-mlx]` / `[dictation-llama]`
    — landed by HS-0 follow-up (see HS-1-04 task list).

## Acceptance criteria

- [x] `LLMRuntime` Protocol defined with `backend`, `load()`, `info()`,
      `classify(prompt, schema, *, max_tokens, temperature)`.
- [x] `MlxRuntime` and `LlamaCppRuntime` both implement the Protocol
      (verified via `isinstance(rt, LLMRuntime)` at the factory) and
      both produce outputs from the same value set in the cross-backend
      equivalence test (mocked at the model level, real at the
      schema-compiler level).
- [x] `auto` resolution returns `mlx` on `darwin/arm64` when `mlx_lm`
      is importable, `llama_cpp` otherwise. Explicit `mlx` / `llama_cpp`
      values raise `RuntimeUnavailableError` with a clear remediation
      message when the requested backend is unavailable.
- [x] `grammars.to_gbnf` produces a string accepted by
      `LlamaGrammar.from_string` for the fixture `BlockSet` — verified
      by `test_to_gbnf_validates_with_llama_grammar_when_available`,
      which is `pytest.importorskip`'d when `llama_cpp` isn't installed
      in the dev env (skipped here; gated again in the integration
      harness).
- [x] `grammars.to_outlines` produces a JSON-schema artifact the `mlx`
      runtime accepts for constrained sampling (verified end-to-end
      against a fake `JSONLogitsProcessor` and via JSON-validity
      round-trip).
- [x] Cross-backend equivalence test: a fixed prompt and fixture
      `BlockSet` produce outputs from the same value set across both
      runtimes (block-id ∈ taxonomy; `extras` keys per schema).
- [x] No stage-side import of `llama_cpp` or `mlx_lm` anywhere — only
      `runtime_llama_cpp.py` / `runtime_mlx.py` reach for them, and
      both imports are lazy inside resolver methods.
- [x] `uv run pytest -q tests/unit/test_dictation_runtime.py
      tests/unit/test_dictation_grammars.py` → 29 passed, 1 skipped
      (the `llama_cpp`-gated GBNF compile case).

## Test plan

- **Unit:**
  - `test_dictation_runtime.py` — `auto` resolution matrix; explicit
    backend failure surfaces; mocked `classify()` round-trip on each
    backend.
  - `test_dictation_grammars.py` — schema → GBNF compile; schema →
    outlines compile; equivalence over fixture `BlockSet`.
- **Integration:**
  - `tests/integration/test_runtime_mlx.py` (skipped without
    `requires_mlx` + model present) — load `Qwen3-8B-MLX-4bit`, run a
    single classify, assert structurally-valid JSON.
  - `tests/integration/test_runtime_llama_cpp.py` (skipped without
    `requires_llama_cpp` + model present) — same, against
    `Qwen2.5-3B-Instruct-Q4_K_M.gguf`.
- **Manual:** None at this story; HS-1-07 covers the end-to-end path.

## Notes / open questions

- The `outlines` library is accepted as a localized dependency for the
  `mlx` runtime path (supersedes the prior "no outlines" decision per
  the 2026-04-25 amendment). Churn risk is contained to
  `runtime_mlx.py` + the `to_outlines` emitter.
- Models are downloaded manually per spec §13 risk #7. Test paths look
  at `~/Models/mlx/Qwen3-8B-MLX-4bit/` and
  `~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf`; integration tests
  skip cleanly when either is missing.
- The existing `holdspeak/intel.py` already wraps `llama-cpp-python` for
  the meeting-intel path. The dictation runtime keeps a separate
  instance (per §3.2 #5) but reuses the loader-failure / Metal-detection
  patterns. No shared model file in DIR-01.
