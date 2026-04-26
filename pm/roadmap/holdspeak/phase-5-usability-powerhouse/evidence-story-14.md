# Evidence — HS-5-14: Runtime guidance copy bundle

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-14
- **Captured at HEAD:** `359ec05` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Guidance bundle** — shared runtime guidance now includes
  `command_bundle`, a newline-joined copy target for all setup commands.
- **Browser copy-all action** — `/dictation` renders **Copy all setup
  commands** for multi-command runtime guidance while keeping individual
  copy buttons.
- **Coverage** — tests assert missing-model bundles include the model
  download command and that the page contains the copy-all wiring.

## Tests

Focused guidance/readiness sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py
..............                                                           [100%]
14 passed in 0.57s
```

Broader web-dictation setup sweep:

```
$ uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
............................................
............................ [ 60%]
................................................                         [100%]
120 passed in 3.04s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1106 passed, 13 skipped in 23.58s
```

New coverage:

- shared runtime guidance exposes `command_bundle`
- missing-model guidance bundle includes `huggingface-cli download`
- `/dictation` contains the copy-all setup button wiring

## Notes

No setup commands are executed by this change.
