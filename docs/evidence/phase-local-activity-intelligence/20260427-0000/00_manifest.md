# Phase 8 Evidence Bundle

Phase: Local Activity Intelligence
Generated: 2026-04-27
Commit range at creation: `1cb9fac..HEAD`

## Files

- `02_git_status.txt` - working tree status before closure edits.
- `10_focused_activity.log` - focused local activity intelligence tests.
- `20_full_regression.log` - full non-Metal regression.
- `30_diff_check.log` - whitespace check output.
- `99_phase_summary.md` - human-readable phase summary.

## Verification Commands

```bash
uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_activity_mapping.py tests/unit/test_db.py tests/integration/test_web_activity_api.py
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
git diff --check
```
