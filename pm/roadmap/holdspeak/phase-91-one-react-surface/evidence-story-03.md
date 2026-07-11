# HS-91-03 evidence — Arrival and configuration

Captured 2026-07-10 during the branch integration validation.

```text
$ uv run pytest tests/integration/ -q --tb=short
689 passed, 3 skipped, 1 warning in 153.34s (0:02:33)

$ npm --prefix web run check
Test Files  13 passed (13)
Tests  109 passed (109)
✓ built in 1.28s
```

The optional-model skips require local ML dependencies; the arrival, setup, settings, and profile integration coverage passed.
