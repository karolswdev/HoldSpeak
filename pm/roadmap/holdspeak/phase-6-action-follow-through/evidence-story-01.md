# HS-6-01 Evidence - Action Item Provenance Audit

## Shipped Result

HS-6-01 mapped the action item follow-through surfaces and closed the
first concrete provenance gap. Action items already persisted
`source_timestamp`; this story now carries that field through the
cross-meeting/project summary APIs and renders it in the history UI.

## Audit Map

- Persistence:
  - `holdspeak/db.py` defines `action_items.source_timestamp`.
  - `holdspeak/db.py` stores generated action item timestamps from both
    object and dict-shaped meeting intelligence outputs.
  - `holdspeak/db.py` now includes `source_timestamp` on
    `ActionItemSummary`, `list_action_items()`, and
    `get_project_action_items()`.
- APIs:
  - `holdspeak/web_server.py` exposes `source_timestamp` from
    `GET /api/all-action-items`.
  - `holdspeak/web_server.py` preserves the same field in global
    action-item status, review, and edit mutation responses.
  - `holdspeak/web_server.py` exposes `source_timestamp` from
    `GET /api/projects/{project_id}/action-items`.
  - Live meeting action-item review/edit APIs already existed under
    `/api/action-items/*` and are covered by `tests/integration/test_intel_streaming.py`.
- Browser:
  - `holdspeak/static/history.html` now renders source timestamp pills in
    the global Action Items tab.
  - `holdspeak/static/history.html` now renders source timestamp pills in
    project action-item lists.
  - `holdspeak/static/history.html` now renders source timestamp pills in
    selected meeting action-item details.
- Tests:
  - `tests/integration/test_web_server.py` pins the history UI shell and
    global action-item API payloads.

## Gaps Found

- Review-state persistence and API mutation paths already exist; HS-6-02
  should focus on browser review ergonomics and context, not new storage.
- Artifact/action linking is still a separate browser workflow gap and
  remains in HS-6-04.
- There is still no external task-system sync by design for Phase 6.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems"
4 passed, 68 deselected in 0.93s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py
114 passed in 2.72s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1107 passed, 13 skipped in 23.27s
```
