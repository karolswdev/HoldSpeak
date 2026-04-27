# HS-8-07 Evidence - Project Activity Mapping Rules

## Shipped Result

HS-8-07 adds deterministic project mapping rules for the local activity
ledger.

The implementation adds:

- `activity_project_rules` schema and migration at DB schema version 13
- `ActivityProjectRule` persistence model
- rule CRUD methods with project FK validation
- deterministic matcher module for domain, URL/title substring, entity
  type, entity ID prefix, GitHub repo, and source-browser rules
- priority-ordered first-match semantics
- preview support for proposed rules before persistence or backfill
- apply/backfill support for existing `activity_records.project_id`
- import-time project assignment after entity extraction
- `/api/activity/project-rules` CRUD APIs
- `/api/activity/project-rules/preview`
- `/api/activity/project-rules/apply`
- `/activity` project-rule editor with preview, edit, disable, delete,
  and apply controls

## Behavior

Rules are evaluated by descending `priority`, then oldest `created_at`.
Disabled rules are ignored. The first enabled match assigns the record's
`project_id`.

Matching is deterministic and local-only. No fuzzy classification, LLM
calls, external API calls, cookies, credentials, page bodies, or hidden
network enrichment were added.

## Verification

```text
uv run pytest -q tests/unit/test_activity_mapping.py tests/unit/test_activity_history.py tests/unit/test_db.py tests/integration/test_web_activity_api.py
75 passed in 4.31s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1155 passed, 13 skipped in 25.62s
```

```text
git diff --check
```
