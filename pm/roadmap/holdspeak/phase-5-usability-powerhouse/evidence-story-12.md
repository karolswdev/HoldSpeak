# Evidence — HS-5-12: Runtime guidance shared source

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-12
- **Captured at HEAD:** `65de341` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Shared guidance helper** — dictation runtime install/model command
  construction now lives in `holdspeak.plugins.dictation.guidance`.
- **Browser reuse** — `/api/dictation/readiness` uses the shared helper
  for `runtime_unavailable` and `runtime_model_missing` guidance.
- **Doctor reuse** — `holdspeak doctor` uses the same helper for its
  terminal-facing fix strings.
- **Focused coverage** — added unit tests for the shared guidance,
  including the macOS arm64 Metal `llama_cpp` command.

## Tests

Guidance-focused sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py
......................................                                   [100%]
38 passed in 0.77s
```

Broader doctor + web-dictation setup sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_dictation_cold_start_cap.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
..............................................
.......................... [ 60%]
................................................                         [100%]
120 passed in 2.80s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1104 passed, 13 skipped in 22.92s
```

New coverage:

- shared `llama_cpp` install command uses Metal flags on macOS arm64
- `auto` runtime guidance offers backend install commands
- doctor model guidance reuses the shared model download command

## Notes

No setup commands are executed by this change.
