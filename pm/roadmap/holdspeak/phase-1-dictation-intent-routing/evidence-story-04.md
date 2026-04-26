# Evidence — HS-1-04 (Pluggable LLM runtime + structured output)

**Story:** [story-04-runtime.md](./story-04-runtime.md)
**Date:** 2026-04-25
**Status flipped:** in-progress → done

## What shipped

- `holdspeak/plugins/dictation/runtime.py` — `LLMRuntime` Protocol
  (`@runtime_checkable`), `RuntimeUnavailableError`, `resolve_backend`
  (auto + explicit, with deterministic test seams), `build_runtime`
  factory with backend-specific kwargs and a lazy default factory
  registry. No backend imports at module top.
- `holdspeak/plugins/dictation/runtime_llama_cpp.py` — `LlamaCppRuntime`
  wrapping `Llama.create_completion(grammar=...)`. Lazy `Llama` /
  `LlamaGrammar` resolution; mirrors the loader-failure pattern from
  `holdspeak/intel.py`. Surfaces `RuntimeUnavailableError` with
  remediation messages on missing model file, missing package, or load
  exception. Optional idle eviction.
- `holdspeak/plugins/dictation/runtime_mlx.py` — `MlxRuntime` wrapping
  `mlx_lm.load` + `mlx_lm.generate` with an `outlines`-style
  `JSONLogitsProcessor`. `outlines` is imported lazily from inside this
  module only — churn risk is contained per the 2026-04-25 amendment.
- `holdspeak/plugins/dictation/grammars.py` — schema compiler:
  `BlockSpec`, `BlockSet`, `StructuredOutputSchema`,
  `GrammarCompileError`, `to_gbnf`, `to_outlines`, `to_outlines_json`,
  `equivalent_value_sets`. Both emitters compile from the same
  `BlockSet`; the cross-backend equivalence test confirms identical
  block-id and extras-enum domains.
- `holdspeak/config.py` — `LLMRuntimeConfig`,
  `DictationPipelineConfig`, `DictationConfig` plumbed onto `Config`.
  Default `DictationConfig` has `pipeline.enabled=False` and
  `runtime.backend="auto"` (DIR-C-001 satisfied).
- `tests/unit/test_dictation_runtime.py` — 19 cases.
- `tests/unit/test_dictation_grammars.py` — 10 cases (1 skipped when
  `llama_cpp` isn't installed locally).
- `tests/integration/test_runtime_llama_cpp.py` — model-gated harness
  marked `requires_llama_cpp`; skipped cleanly without the GGUF.
- `tests/integration/test_runtime_mlx.py` — model-gated harness marked
  `requires_mlx`; skipped cleanly without the snapshot or `outlines`.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-C-001` Defaults keep DIR-01 fully off | `test_default_dictation_pipeline_disabled` |
| `DIR-A-003` (partial) Doctor reports runtime status | runtime exposes `info()` / structured errors; doctor wiring lands in HS-1-09 |
| Backend Protocol surface (§7.1) | `test_build_runtime_returns_llmruntime_protocol_conformant_object`, mlx/llama factory tests |
| Auto resolution (§7.1) | `test_auto_prefers_mlx_on_arm64_when_importable`, `test_auto_falls_back_to_llama_cpp_when_mlx_missing`, `test_auto_picks_llama_cpp_off_arm64`, `test_auto_raises_when_no_backend_available` |
| Explicit-never-falls-back (§7.1) | `test_explicit_backends_never_fall_back`, `test_explicit_mlx_off_arm64_raises_with_remediation`, `test_explicit_mlx_without_mlx_lm_raises`, `test_explicit_llama_cpp_without_lib_raises` |
| GBNF compile (§7.3) | `test_to_gbnf_contains_all_block_ids`, `test_to_gbnf_validates_with_llama_grammar_when_available` (importorskipped here; runs in environments with the extra) |
| Outlines compile (§7.3) | `test_to_outlines_emits_oneof_per_block`, `test_to_outlines_json_is_valid_json_and_round_trips` |
| Cross-backend equivalence (§7.3 item 3) | `test_cross_backend_equivalence_value_sets_match`, `test_both_backends_produce_outputs_in_schema_value_set` |
| No-stage-side imports of llama/mlx | enforced architecturally: stage code does not import these modules (none exists yet); imports live exclusively in `runtime_llama_cpp.py` / `runtime_mlx.py` and are lazy |

## Test output

### Targeted (runtime + grammars)

```
$ uv run pytest -q tests/unit/test_dictation_runtime.py tests/unit/test_dictation_grammars.py
......s.......................                                          [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
29 passed, 1 skipped in 0.04s
```

The skip is `test_to_gbnf_validates_with_llama_grammar_when_available`,
which `pytest.importorskip("llama_cpp")` and exercises
`LlamaGrammar.from_string`. It runs on developer machines with the
`[dictation-llama]` extra installed.

### Full regression

```
$ uv run pytest -q tests/ --timeout=30
...
1 failed, 824 passed, 13 skipped, 3 warnings in 17.32s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

The lone failure is the pre-existing hardware-only Whisper-loader case
in `tests/e2e/test_metal.py` (recorded in HS-1-02 and HS-1-03 evidence).
Skip count grew by 3: two new model-gated integration tests
(`test_runtime_llama_cpp.py`, `test_runtime_mlx.py`) and the `llama_cpp`
GBNF compile case. Pass-count delta: 795 → 824 (+29 new unit cases).

## Files in this commit

- `holdspeak/plugins/dictation/runtime.py` (new)
- `holdspeak/plugins/dictation/runtime_llama_cpp.py` (new)
- `holdspeak/plugins/dictation/runtime_mlx.py` (new)
- `holdspeak/plugins/dictation/grammars.py` (new)
- `holdspeak/config.py` (added `LLMRuntimeConfig`, `DictationPipelineConfig`, `DictationConfig`; threaded onto `Config`)
- `tests/unit/test_dictation_runtime.py` (new)
- `tests/unit/test_dictation_grammars.py` (new)
- `tests/integration/test_runtime_llama_cpp.py` (new)
- `tests/integration/test_runtime_mlx.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-04-runtime.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-04.md` (this file)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- `pyproject.toml` extras (`[dictation-mlx]`, `[dictation-llama]`)
  remain a backlog item per story-04 §"Out". They are not required for
  the unit-test verification above; integration tests skip cleanly
  without them.
- `LLMRuntimeConfig.warm_on_start` is honored by both backend
  constructors (calls `load()` eagerly when set). Callers should leave
  it `False` until the controller is wired (HS-1-07).
- `DictationConfig` was added (not just `LLMRuntimeConfig`) to give
  `holdspeak.config.Config` a single-namespace home for both pipeline
  and runtime knobs. The pipeline config is just the §9.4 dataclass —
  HS-1-07 will read it; HS-1-03's executor takes plain kwargs.
