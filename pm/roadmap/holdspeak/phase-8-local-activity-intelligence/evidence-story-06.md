# HS-8-06 Evidence - Privacy Controls and Retention

## Shipped Result

HS-8-06 adds the visible trust and control layer for Phase 8 local
activity intelligence.

The implementation adds:

- activity privacy settings in the local DB
- default-enabled ingestion state
- pause/resume via API and browser UI
- retention days setting
- domain include/exclude rules
- importer enforcement for global pause and excluded domains
- retained checkpoint advancement for excluded domains to avoid churn
- `/activity` browser surface
- `/api/activity/status`
- `/api/activity/records`
- `/api/activity/refresh`
- `/api/activity/settings`
- `/api/activity/domains`
- `DELETE /api/activity/records`

## Browser Surface

`/activity` now shows:

- enabled or paused state
- discovered readable browser sources
- imported record count
- retention days
- excluded domains
- recent activity records
- refresh control
- pause/resume control
- clear imported records control

The page keeps the feature inspectable while preserving the Phase 8
default-enabled direction for this personal local tool.

## Privacy Behavior

Paused ingestion returns disabled import results and does not read source
history databases.

Excluded domains are matched against exact domains and subdomains. When
an excluded URL is encountered, the importer skips persistence but still
advances the raw checkpoint so repeated imports do not churn over the
same excluded rows.

Retention is enforced after import by deleting records older than the
configured `retention_days` window.

No remote telemetry, network enrichment, cookies, credentials, cache,
private browsing data, or page contents are read.

## Verification

```text
uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py tests/integration/test_web_activity_api.py
81 passed in 2.07s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1145 passed, 13 skipped in 26.67s
```

```text
git diff --check
```
