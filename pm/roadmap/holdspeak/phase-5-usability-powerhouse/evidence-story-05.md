# Evidence — HS-5-05: Browser project switcher polish

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-05
- **Captured at HEAD:** `18da668` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **`GET /api/dictation/project-context`** — validates the current or
  manually supplied project root and returns project metadata plus the
  expected project blocks and project-KB paths.
- **Validated Apply** — `/dictation` now checks the typed project root
  before saving it to localStorage. Invalid paths stay visible with an
  error and do not become the active override.
- **Recent roots** — successful manual roots are stored in
  `holdspeak.recentProjectRoots` and exposed through a Recent roots
  selector in the project-root bar.
- **Fast switching** — selecting a recent root validates and applies it,
  then refreshes the active readiness/blocks/KB/dry-run surface.

## Tests

Focused dictation cockpit sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py
....................................................                     [100%]
52 passed in 1.56s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1092 passed, 13 skipped in 21.12s
```

New coverage:

- project-context endpoint returns metadata and target file paths for a
  valid manual project root
- missing manual root returns a 400 with `project_root` in the error
- no detected cwd project returns 404
- `/dictation` includes the validation endpoint and recent-root control

## Notes

This intentionally avoids server persistence for recent projects. The
feature is browser ergonomics, not a new server-side project registry.
