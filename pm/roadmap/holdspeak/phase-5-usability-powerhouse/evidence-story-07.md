# Evidence — HS-5-07: Project KB starter action

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-07
- **Captured at HEAD:** `d514e26` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **`POST /api/dictation/project-kb/starter`** — creates a canonical
  `.holdspeak/project.yaml` using the existing Project KB validation
  and atomic writer.
- **Starter keys** — the file starts with `stack`, `task_focus`, and
  `constraints` set to `null`, giving users valid placeholder names
  without inventing schema.
- **No overwrite** — if a Project KB file already exists, the starter
  endpoint returns `409` and leaves the file untouched.
- **Project-root override** — the starter action honors the selected
  `project_root`.
- **Browser actions** — `/dictation` now has a Project KB **Use
  starter** button and a readiness **Create starter KB** action for
  missing-KB warnings.

## Tests

Focused web-dictation sweep:

```
$ uv run pytest -q tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
......................................................... [ 97%]
..                                                                       [100%]
74 passed in 2.30s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1097 passed, 13 skipped in 22.65s
```

New coverage:

- starter Project KB creation writes canonical YAML
- project-root override writes to the selected project
- starter endpoint refuses to overwrite existing Project KB
- readiness missing-KB warning includes `kb_action=create_starter`
- `/dictation` exposes both the starter endpoint and readiness starter wiring

## Notes

This keeps readiness read-only. The actual write still happens through
an explicit browser action.
