# Evidence — HS-5-13: Runtime guidance docs route

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-13
- **Captured at HEAD:** `7a5e48e` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Local docs route** — added `/docs/dictation-runtime`, served by the
  web runtime, for dictation LLM setup guidance.
- **Runtime setup page** — added a compact page covering MLX,
  `llama_cpp`, default model paths, model download commands, and the
  macOS arm64 Metal rebuild command.
- **Guidance link update** — shared runtime guidance now points browser
  users to `/docs/dictation-runtime`.

## Tests

Guidance/readiness sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py
.............                                                            [100%]
13 passed in 0.59s
```

Broader web-dictation setup sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
.........................................
............................... [ 60%]
...............................................                          [100%]
119 passed in 3.12s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1105 passed, 13 skipped in 26.34s
```

New coverage:

- shared guidance links target `/docs/dictation-runtime`
- readiness runtime guidance payload exposes the local docs target
- `/docs/dictation-runtime` serves setup content for both dictation
  LLM backends

## Notes

No setup commands are executed by this change.
