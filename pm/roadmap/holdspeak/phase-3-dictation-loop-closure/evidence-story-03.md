# Evidence — HS-3-03: `llama_cpp` end-to-end leg

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-03
- **Captured at HEAD:** `e56202f` (pre-commit)
- **Date:** 2026-04-26

## What shipped

### README documentation (public surface)

`README.md` gained an "Optional: Dictation LLM Backend" section
covering both backends:

- **MLX (Apple Silicon primary):** `uv pip install -e '.[dictation-mlx]'` + `huggingface-cli download mlx-community/Qwen3-8B-MLX-4bit ...`.
- **`llama_cpp` (cross-platform default):** `CMAKE_ARGS="-DGGML_METAL=on" uv pip install -e '.[dictation-llama]'` (Metal rebuild flagged loudly per DIR-01 §12 risk #2) + `huggingface-cli download bartowski/Qwen2.5-3B-Instruct-GGUF Qwen2.5-3B-Instruct-Q4_K_M.gguf ...`.
- Pipeline opt-in JSON snippet for `~/.config/holdspeak/config.json`.
- Verification commands: `holdspeak doctor`, `holdspeak dictation runtime status`, `holdspeak dictation dry-run`.
- Reference to `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md §8` for the block schema and per-project override path.

### End-to-end integration test

New file `tests/integration/test_dictation_llama_cpp_e2e.py`:

- Marked `pytest.mark.requires_llama_cpp` and gated by a
  `_have_model()` predicate that imports `llama_cpp` and stats the
  default GGUF path (`~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf`).
- Builds a temp project tree with `.holdspeak/blocks.yaml` (2 blocks
  whose templates reference `{project.name}`), monkeypatches `$HOME`
  + cwd, calls `assembly.build_pipeline(cfg.dictation, project_root=...)`
  with `cfg.dictation.runtime.backend = "llama_cpp"` and the real
  GGUF path.
- Asserts `runtime_status == "loaded"`, both stages ran (`intent-router`
  + `kb-enricher`), no `{project.name}` placeholder leaked into
  `final_text` (DIR-F-007), and the result is non-empty.
- Tolerates the model legitimately not classifying above threshold
  (DIR-F-001 — confidence below threshold is a valid no-match) so the
  test isn't flaky against model nondeterminism.

This goes one level above the existing
`tests/integration/test_runtime_llama_cpp.py`, which only exercises
`LlamaCppRuntime.classify` directly.

### Doctor (no change required)

Audit confirmed `_check_dictation_runtime` (DIR-DOC-001) and
`_check_dictation_constraint_compile` (DIR-DOC-002) already handle
the `llama_cpp` path correctly:

- DIR-DOC-001: reports `resolved=llama_cpp` + GGUF availability via
  `Path(cfg.runtime.llama_cpp_model_path).expanduser().exists()`.
- DIR-DOC-002: branches on `resolved == "mlx"` → `to_outlines`, else
  → `to_gbnf` (the `llama_cpp` GBNF compile path).

The existing `tests/unit/test_doctor_command.py` has 4 tests
stubbing `resolve_backend → ("llama_cpp", "stubbed")` for both
checks, all passing in this session's regression sweep. No
extension shipped; documented in the story's AC for the next
operator's audit.

## Test output

### Targeted (the new gated e2e test)

```
$ uv run pytest tests/integration/test_dictation_llama_cpp_e2e.py -v --timeout=30
... (output snipped)
collected 1 item
tests/integration/test_dictation_llama_cpp_e2e.py::test_full_pipeline_runs_through_llama_cpp_with_project_context SKIPPED [100%]
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf are required for this integration test
============================== 1 skipped in 0.03s ==============================
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
988 passed, 13 skipped in 16.84s
```

Pass delta vs. HS-3-02 baseline (988 passed, 12 skipped): **+0
passed, +1 skipped**. The new gated test joins the 12 pre-existing
skips. No regressions. The total +15 cumulative pass delta vs.
HS-3-scaffold baseline (973) is unchanged because HS-3-03 ships no
new always-running tests — its value is the gated path that runs on
the reference machine.

## Gated-test execution policy

Per DIR-01 §13 risk #7 and the standing
`feedback_no_validation_spikes` memory, the gated e2e test was
authored, gated cleanly, and verified to skip on the dev box. The
**user runs it against the real GGUF** on the reference Mac during
ongoing dogfood; this evidence file does not include a passing
run-output because the dev box doesn't carry the GGUF (~3 GB) and
fetching it just to satisfy the bundle would be measurement
ceremony per the standing memory.

If a future operator wants confirmation: install the extra +
download the GGUF per the README, then run:

```bash
uv run pytest tests/integration/test_dictation_llama_cpp_e2e.py -v --timeout=120
```

The expected outcome is a `PASSED` result with both
`intent-router` and `kb-enricher` stages running through the real
GGUF.

## Deviations from story scope

- The story's "smoke-run log" deliverable is documented as a deferred
  capture — see "Gated-test execution policy" above. The test exists,
  is gated, and runs when deps are present.
- No extension to `_check_dictation_constraint_compile` (DIR-DOC-002)
  was required; existing coverage already validates the `llama_cpp`
  GBNF compile path. Story scope explicitly invited "extend it if the
  backend-resolution path doesn't already report it" — it does, so
  no extension shipped.

## Out-of-scope (deferred per story)

- Latency benchmarks against DIR-01 §6 targets — explicitly forbidden
  by the standing no-pre-shipping-measurement-gate convention.
- GGUF file shipped in the repo — too large; download path documented
  in README instead.
- Cloud or alternate backend wiring.
