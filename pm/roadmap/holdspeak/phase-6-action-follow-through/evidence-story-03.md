# HS-6-03 Evidence - Action Item Filters and Open-Work View

## Shipped Result

HS-6-03 makes the Actions tab a focused open-work surface:

- The default action-item view is now pending items that still need
  review.
- A review-state filter allows switching between Needs review, Accepted,
  and All review states.
- The existing status filter continues to support all/pending/done/
  dismissed states.
- The Open Work button resets the view back to pending needs-review work.
- Empty-state copy now reflects the active open-work filters.

## Files

- `holdspeak/static/history.html`
  - adds `actionReviewFilter`.
  - defaults `actionStatusFilter` and `actionReviewFilter` to pending
    follow-through work.
  - adds `showOpenActionWork()` and `actionItemsEmptyMessage()`.
  - applies status and review filters when loading action items.
- `tests/integration/test_web_server.py`
  - pins the new browser filter wiring in the history UI smoke test.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems"
4 passed, 68 deselected in 0.49s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py
114 passed in 2.11s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1107 passed, 13 skipped in 22.51s
```
