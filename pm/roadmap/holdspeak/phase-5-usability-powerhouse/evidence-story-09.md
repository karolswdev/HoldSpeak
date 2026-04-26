# Evidence — HS-5-09: Model/runtime install guidance

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-09
- **Captured at HEAD:** `2c8b7ab` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Structured runtime guidance** — readiness now attaches a
  `guidance` payload to `runtime_unavailable` warnings with
  backend-specific install commands.
- **Structured model guidance** — `runtime_model_missing` warnings now
  include the exact missing `model_path`, a suggested next step, and
  copyable local command snippets.
- **Browser rendering** — `/dictation` renders guidance blocks in the
  Readiness warning list and in the Runtime panel. Commands are copied
  by explicit user action only.

## Tests

Focused web-dictation sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
................................................ [ 82%]
...............                                                          [100%]
87 passed in 2.50s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1099 passed, 13 skipped in 23.46s
```

New coverage:

- missing-model readiness warning includes `guidance.kind=missing_model`
  and the exact missing path
- unavailable-runtime readiness warning includes install guidance for
  the selected backend
- `/dictation` includes Runtime guidance wiring and copy-command buttons

## Notes

No automatic package installation or model download was added.
