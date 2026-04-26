# Evidence — HS-5-11: Doctor runtime guidance parity

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-11
- **Captured at HEAD:** `e862f5b` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Install command guidance** — `holdspeak doctor` now reports
  backend-specific `uv pip install -e ...` commands when dictation LLM
  runtime resolution fails.
- **Model command guidance** — missing-model warnings now include a
  `huggingface-cli download` command and the target model directory.
- **Metal guidance preserved** — macOS arm64 `llama_cpp` guidance keeps
  the `CMAKE_ARGS="-DGGML_METAL=on"` install command.

## Tests

Doctor unit sweep:

```
$ uv run pytest -q tests/unit/test_doctor_command.py
..........................                                               [100%]
26 passed in 0.29s
```

Focused doctor + adjacent dictation setup sweep:

```
$ uv run pytest -q tests/unit/test_doctor_command.py tests/integration/test_dictation_cold_start_cap.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py
........................................
................................ [ 98%]
.                                                                        [100%]
73 passed in 1.77s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1100 passed, 13 skipped in 23.96s
```

New coverage:

- unavailable dictation runtime doctor warning includes a `uv pip`
  install command for the selected backend
- missing dictation model doctor warning includes a `huggingface-cli`
  command and target directory

## Notes

Doctor remains read-only. It reports commands; it does not run them.
