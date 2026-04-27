# HS-9-04 Evidence - GitHub CLI Enrichment Annotations

Date: 2026-04-27

## Delivered

- Added `holdspeak.activity_github` for read-only `gh` command planning and execution.
- Added local web APIs for GitHub enrichment connector state, preview, enablement, and guarded runs:
  - `GET /api/activity/enrichment/connectors`
  - `PUT /api/activity/enrichment/connectors/gh`
  - `GET /api/activity/enrichment/github/preview`
  - `POST /api/activity/enrichment/github/run`
- The `gh` connector is created disabled by default.
- Preview exposes command path/availability and the exact read-only `gh pr view` / `gh issue view` commands before any annotation write.
- Run requires explicit connector enablement, applies timeout/output caps, and writes local `activity_annotations`.

## Verification

```text
$ uv run pytest -q tests/unit/test_activity_github.py
...                                                                      [100%]
3 passed in 0.11s
```

```text
$ uv run pytest -q tests/integration/test_web_activity_api.py -k "github_enrichment"
..                                                                       [100%]
2 passed, 9 deselected in 0.63s
```

```text
$ git diff --check
```
