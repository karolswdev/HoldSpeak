# Evidence — HS-5-08: Runtime readiness action

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-08
- **Captured at HEAD:** `410d58b` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Actionable disabled-pipeline warning** — readiness now includes
  `runtime_action: enable_pipeline` for `pipeline_disabled`.
- **Browser action** — `/dictation` renders an **Enable pipeline**
  button for that warning. It switches to Runtime, loads current
  settings into the form, checks the enable box, and saves through
  `PUT /api/settings`.
- **Config preservation** — added integration coverage that partial
  settings updates enabling the pipeline preserve existing runtime
  backend/model configuration.

## Tests

Focused web-dictation sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
............................................................ [ 83%]
..............                                                           [100%]
86 passed in 2.77s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1098 passed, 13 skipped in 24.57s
```

New coverage:

- disabled-pipeline readiness warning carries `runtime_action=enable_pipeline`
- `/dictation` exposes readiness runtime-action wiring
- partial settings PUT can enable pipeline while preserving runtime backend

## Notes

This keeps runtime mutation centralized in `/api/settings`; readiness
only describes the action to offer.
