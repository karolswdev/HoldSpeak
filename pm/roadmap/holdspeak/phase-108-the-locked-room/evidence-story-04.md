# Evidence - HS-108-04

- **Story:** HS-108-04 - Reads arrive with a principal
- **Status:** done
- **Date:** 2026-07-29

## Captured proof

```text
$ uv run --extra test pytest -q tests/unit/test_activity_github.py tests/unit/test_activity_jira.py tests/unit/test_pipeline_runner.py tests/unit/test_web_routes_missioncontrol.py
.......................................................................  [100%]
71 passed in 2.72s
```

Negative cases pass `UNAUTHENTICATED` or an untrusted agent and assert the
fake `gh`, `jira`, or `dw` runner was never called. One full-unit finding
was fixed here: `ReadSubprocessDenied` subclasses `PermissionError`, which
subclasses `OSError`; the bridge now re-raises the named denial before its
ordinary CLI-unavailable handler.
