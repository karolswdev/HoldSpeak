# HS-91-04 evidence — Dictation cockpit

Captured 2026-07-10 during the branch integration validation.

```text
$ uv run pytest tests/integration/ -q --tb=short
689 passed, 3 skipped, 1 warning in 153.34s (0:02:33)

$ uv run pytest tests/unit/ -q --tb=short
2790 passed in 66.64s (0:01:06)
```

The integration cohort includes the dictation runtime, settings, journal, correction, learning, readiness, and moment-of-truth coverage.
