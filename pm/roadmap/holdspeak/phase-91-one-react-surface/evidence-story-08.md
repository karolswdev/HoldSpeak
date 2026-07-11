# HS-91-08 evidence — Studio and support surfaces

Captured 2026-07-10 during the branch integration validation.

```text
$ npm --prefix web run check
Test Files  13 passed (13)
Tests  109 passed (109)
✓ built in 1.28s

$ uv run pytest tests/e2e/ -q --tb=short -m 'e2e and not metal'
17 passed, 2 skipped, 50 deselected in 79.06s (0:01:19)
```

Workbench, Presence, Studio, Companion, and documentation routes are included in the React route and browser cohorts.
