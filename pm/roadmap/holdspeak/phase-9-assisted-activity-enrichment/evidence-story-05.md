# HS-9-05 Evidence - Jira CLI Enrichment Annotations

Date: 2026-04-28

## Delivered

- Added `holdspeak.activity_jira` for read-only `jira` command planning and execution.
- Added local web APIs for Jira enrichment preview and guarded runs:
  - `GET /api/activity/enrichment/jira/preview`
  - `POST /api/activity/enrichment/jira/run`
- Extended connector APIs so `jira` is visible and disabled by default alongside `gh`.
- Preview exposes command path/availability and exact read-only `jira issue view KEY --plain` commands before any annotation write.
- Run requires explicit connector enablement, applies timeout/output caps, accepts JSON or raw capped CLI output, and writes local `activity_annotations`.

## Verification

```text
$ uv run pytest -q tests/unit/test_activity_jira.py
....                                                                     [100%]
4 passed in 0.17s
```

```text
$ uv run pytest -q tests/integration/test_web_activity_api.py -k "jira_enrichment"
..                                                                       [100%]
2 passed, 11 deselected in 0.73s
```

```text
$ git diff --check
```
