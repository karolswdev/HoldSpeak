# HS-8-09 Evidence - DoD Sweep and Phase Exit

## Shipped Result

HS-8-09 closes Phase 8 with an evidence bundle, focused local activity
intelligence verification, full non-Metal regression, and roadmap status
updates.

Phase evidence bundle:

- `docs/evidence/phase-local-activity-intelligence/20260427-0000/`

Bundle contents:

- `00_manifest.md`
- `02_git_status.txt`
- `10_focused_activity.log`
- `20_full_regression.log`
- `30_diff_check.log`
- `99_phase_summary.md`

## Phase Result

Phase 8 delivered a private, local-first Local Attention Ledger:

- Safari/Firefox browser-history source audit
- normalized activity ledger persistence
- read-only browser history readers
- deterministic work entity extraction
- plugin-visible activity context
- `/activity` privacy controls and retention
- project activity mapping rules
- assisted enrichment connector design

## Verification

```text
uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_activity_mapping.py tests/unit/test_db.py tests/integration/test_web_activity_api.py
91 passed in 2.59s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1155 passed, 13 skipped in 27.84s
```

```text
git diff --check
```
