# Evidence — HS-5-01: Dictation project-root override

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-01
- **Captured at HEAD:** `0868153` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **`holdspeak/web_server.py`** — added shared project-context
  resolution for dictation project APIs. `project_root` can point at
  another existing local directory; if no known anchor is present, the
  explicit directory is treated as a manual project root.
- **Project blocks API** — `GET/POST/PUT/DELETE /api/dictation/blocks`
  accepts `project_root` when `scope=project`.
- **Project KB API** — `GET/PUT/DELETE /api/dictation/project-kb`
  accepts `project_root`; PUT can create `.holdspeak/project.yaml`
  under the selected root.
- **Dry-run API** — `POST /api/dictation/dry-run` accepts optional
  `project_root`, validates the field type, and uses that project's
  blocks and KB.
- **`holdspeak/static/dictation.html`** — added Project root
  apply/clear controls. The override is stored in localStorage and
  shared across project block CRUD, Project KB, and Dry-run.

## Tests

```
$ uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
.....................................................                    [100%]
53 passed in 1.52s
```

Full regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1076 passed, 13 skipped in 19.69s
```

New coverage:

- `test_project_root_override_selects_project_without_relaunch` in blocks API tests.
- `test_project_root_override_selects_project_without_relaunch` in project-KB tests.
- `test_dry_run_project_root_override_selects_project_without_relaunch`.
- `test_dry_run_rejects_non_string_project_root`.
- `/dictation` page smoke now asserts the project-root override control exists.

## Notes

This deliberately avoids compatibility branches. `project.yaml` stays
canonical as `kb: {...}`.
