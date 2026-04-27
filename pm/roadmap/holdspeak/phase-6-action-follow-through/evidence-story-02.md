# HS-6-02 Evidence - Action Item Review Controls

## Shipped Result

HS-6-02 made action-item review state editable from the browser
follow-through surfaces that show action items:

- Global Action Items tab can accept an item or mark an accepted item
  back to needs review.
- Project action-item lists now show review state next to source
  provenance and expose the same review controls.
- Selected meeting detail action items now expose the same review
  controls next to source provenance.

The implementation reuses the existing
`PATCH /api/all-action-items/{item_id}/review` endpoint and refreshes the
global list, selected meeting detail, and selected project action-item
list after mutation.

## Files

- `holdspeak/static/history.html`
  - adds reusable `setActionReviewState(item, reviewState)`.
  - refreshes selected project action items after review/edit updates.
  - renders Accept / Mark Needs Review controls in global, project, and
    selected meeting action-item surfaces.
- `tests/integration/test_web_server.py`
  - pins the browser wiring strings in the history UI smoke test.
  - covers accepting and returning a global action item to pending review.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems"
4 passed, 68 deselected in 0.56s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py
114 passed in 3.73s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1107 passed, 13 skipped in 27.30s
```
