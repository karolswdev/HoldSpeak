# Evidence — HS-5-10: Current cwd project visibility

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-10
- **Captured at HEAD:** `6641711` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Cwd visibility on load** — `/dictation` now calls
  `/api/dictation/project-context` on startup when no manual override is
  active and shows the detected project name, anchor, and root in the
  project banner.
- **Override clarity preserved** — saved manual overrides still display
  as selected overrides instead of being replaced by cwd detection.
- **Use-cwd refresh** — clearing the override or applying an empty
  override re-runs cwd project visibility.

## Tests

Focused project-switcher/block sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_blocks_api.py
.....................................                                    [100%]
37 passed in 1.34s
```

Focused web-dictation sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
.................................................. [ 81%]
................                                                         [100%]
88 passed in 2.66s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1100 passed, 13 skipped in 23.74s
```

New coverage:

- cwd project-context API returns detected project details without
  `project_root`
- `/dictation` includes cwd-project visibility wiring

## Notes

No project detection semantics changed; this is a browser visibility
improvement over the existing endpoint.
