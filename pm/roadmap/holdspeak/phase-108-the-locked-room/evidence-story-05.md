# Evidence - HS-108-05

- **Story:** HS-108-05 - Silence ends, and CI watches
- **Status:** done
- **Date:** 2026-07-29

## Captured proof

```text
$ HOLDSPEAK_REQUIRE_LIVE_BUS=1 uv run --extra test pytest -q tests/e2e/test_live_bus.py
...                                                                      [100%]
3 passed in 25.32s
```

```text
$ uv run --extra test pytest -q tests/unit/test_kernel_broker.py tests/unit/test_live_bus_ci_gate.py
(included in the 41-test guard capture in evidence-story-06)
```

The broker tests cover never-claimed refusal, claimed-silent
indeterminate, idempotent reaping, revoked warrants, and immutable late
receipts. The workflow guard pins Node setup, `npm ci`, production build,
Chromium installation, the hard-require environment variable, and the
dedicated no-skip test invocation.
