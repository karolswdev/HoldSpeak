# HS-5-11 — Doctor runtime guidance parity

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-10
- **Unblocks:** fixing runtime setup from `holdspeak doctor` without opening the browser
- **Owner:** codex

## Problem

HS-5-09 made browser readiness warnings actionable for missing
dictation runtime dependencies and model files. `holdspeak doctor`
still warned about those same states with generic prose, which means
terminal-first setup lacked the same copyable next steps.

## Scope

- **In:**
  - Add backend-specific install commands to the `LLM runtime` doctor
    warning when runtime resolution fails.
  - Add model download commands to the `LLM runtime` doctor warning
    when the selected model path is missing.
  - Preserve doctor as a read-only check; do not install packages or
    download models.
- **Out:**
  - New doctor command flags.
  - Changing doctor exit-code policy.
  - Loading the LLM model from doctor.

## Acceptance Criteria

- [x] Missing runtime backend warnings include concrete `uv pip` install commands.
- [x] Missing model warnings include concrete `huggingface-cli download` commands and the target directory.
- [x] The macOS arm64 `llama_cpp` install guidance keeps the Metal rebuild command.
- [x] Doctor remains read-only and does not load the model.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_doctor_command.py`
- `uv run pytest -q tests/unit/test_doctor_command.py tests/integration/test_dictation_cold_start_cap.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This is doctor/readiness parity for setup guidance. Runtime mutation
  still happens only through the existing config paths.
