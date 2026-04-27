# HS-8-04 Evidence - Work Entity Extractors

## Shipped Result

HS-8-04 adds deterministic local work-entity extraction for browser
activity records.

The implementation adds `holdspeak/activity_entities.py` with extractors
for:

- Jira tickets from issue URLs and safe Jira/Atlassian title fallback
- Miro boards
- GitHub pull requests
- GitHub issues
- Linear issues
- Confluence/Atlassian pages
- Google Docs
- Google Sheets
- Google Drive files
- Notion pages
- generic domain fallback records

`holdspeak/activity_history.py` now calls the extractor during Safari and
Firefox imports and stores `entity_type` and `entity_id` through the
HS-8-02 activity ledger API.

## Determinism and Privacy

The extractors use URL/title parsing only. There are no network calls,
OAuth flows, browser cookies, page content reads, LLM calls, or external
API integrations.

Jira title fallback is intentionally limited to Jira/Atlassian-like
domains so unrelated pages that mention strings like `HS-804` do not
become Jira tickets.

Unknown HTTP(S) URLs fall back to stable generic domain entities so the
ledger still has useful grouping data without fabricating a specific work
object.

## Verification

```text
uv run pytest -q tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py
69 passed in 1.79s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1133 passed, 13 skipped in 23.68s
```

```text
git diff --check
```
