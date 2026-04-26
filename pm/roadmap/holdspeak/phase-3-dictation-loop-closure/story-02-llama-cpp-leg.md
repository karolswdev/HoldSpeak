# HS-3-02 — `llama_cpp` end-to-end leg

- **Project:** holdspeak
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HS-3-01 (project context flowing so the leg exercises a realistic utterance)
- **Unblocks:** the cross-platform default declared in DIR-01 §5; Linux x86_64 secondary support
- **Owner:** unassigned

## Problem

DIR-01 §5 declares `llama_cpp` (Qwen2.5-3B-Instruct-Q4_K_M) the
cross-platform default. `holdspeak/plugins/dictation/runtime_llama_cpp.py`
exists (156 lines) and the `[dictation-llama]` extra is declared in
`pyproject.toml`, but there's no verified end-to-end run on a real
GGUF: the existing `tests/.../test_runtime_llama_cpp.py` skips when
`llama_cpp` + the GGUF aren't installed (per the handover, this is
one of the 12 currently-skipped tests). This story closes that loop
so the cross-backend default is real, not aspirational.

## Scope

- **In:**
  - Document the install path: `uv pip install -e '.[dictation-llama]'` on macOS arm64 with the Metal `CMAKE_ARGS` rebuild guidance from DIR-01 §12 risk #2; GGUF download command/URL captured in the README dictation section.
  - Integration test gated on a `requires_llama_cpp` marker, exercising the full pipeline: Utterance → router → kb-enricher → assembly → final text, with the LLM stage running through `runtime_llama_cpp.py` against the configured GGUF.
  - Verify the `DIR-DOC-002` doctor check (structured-output GBNF compilation) lights up correctly when the `llama_cpp` backend is selected — extend it if the backend-resolution path doesn't already report it.
  - Capture a smoke-run log in evidence showing one classify call returning a structured response.
- **Out:**
  - Benchmarks against DIR-01 §6 latency targets — per the standing no-pre-shipping-measurement-gate convention.
  - Adding the `llama_cpp` model files to the repo.
  - Cloud or alternate backend wiring.

## Acceptance criteria

- [ ] README dictation section documents the `[dictation-llama]` install + GGUF download path.
- [ ] An integration test marked `requires_llama_cpp` exists at `tests/integration/test_dictation_llama_cpp_e2e.py` (or similar) and runs the full pipeline against a real GGUF when the marker passes.
- [ ] On a machine without `llama_cpp` installed, the test is skipped (not failed).
- [ ] `holdspeak doctor` reports the resolved backend + GGUF load status when `dictation.runtime.backend = llama_cpp` is set.
- [ ] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.

## Test plan

- **Integration (gated):** the new e2e test, with `requires_llama_cpp` marker registered in `pyproject.toml` or `conftest.py`.
- **Doctor:** unit test asserting the backend-resolution + GGUF-load status surface.
- **Regression:** the documented full-suite command (metal excluded).

## Notes / open questions

- The story author should run the gated e2e test on the reference Mac during implementation (with the GGUF downloaded). Capture the output in evidence so the deferred-from-skipped status is explicit.
- The Metal-wheel mismatch risk (DIR-01 §12 #2) is the most likely real-world failure. The doctor surface should make it diagnosable in one command.
