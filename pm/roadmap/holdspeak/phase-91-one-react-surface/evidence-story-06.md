# HS-91-06 evidence — Live meeting room

Captured 2026-07-10 during the branch integration validation.

```text
$ uv run pytest tests/e2e/ -q --tb=short -m 'e2e and not metal'
17 passed, 2 skipped, 50 deselected in 79.06s (0:01:19)

$ uv run pytest tests/e2e/test_live_bus.py -q --tb=short
3 passed in 21.61s
```

The two skips are explicit opt-in spoken tests. The real browser runtime bus, reconnect, and broadcast paths passed.
