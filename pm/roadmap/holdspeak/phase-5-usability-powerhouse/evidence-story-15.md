# Evidence — HS-5-15: Runtime docs backend deep links

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-15
- **Captured at HEAD:** `325ca76` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Backend anchors** — the local runtime setup page now exposes
  `#mlx` and `#llama-cpp` anchors.
- **Shared target helper** — runtime guidance now computes docs targets
  through a shared helper.
- **Context-aware links** — known MLX/`llama_cpp` guidance links jump
  directly to the matching setup section, while `auto` still links to
  the top-level docs page.

## Tests

Focused guidance/readiness sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py
...............                                                          [100%]
15 passed in 0.53s
```

Broader web-dictation setup sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
...............................................
......................... [ 59%]
.................................................                        [100%]
121 passed in 2.86s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1107 passed, 13 skipped in 21.08s
```

New coverage:

- shared docs target helper returns backend anchors
- missing-model guidance links to `/docs/dictation-runtime#llama-cpp`
- docs route includes both backend anchor IDs

## Notes

No runtime setup commands changed.
