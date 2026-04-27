# HS-7-04 Evidence - Handoff Export Docs

## Shipped Result

HS-7-04 documents the local handoff export workflow:

- README now lists the saved-meeting export API.
- README explains that `/history` selected meeting detail can download
  local Markdown/JSON handoff files.
- Meeting Mode Guide lists the export API and the post-meeting handoff
  workflow.
- Both docs clarify that this workflow produces local downloads only and
  does not publish to external systems.

## Files

- `README.md`
- `docs/MEETING_MODE_GUIDE.md`

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or meeting_export_endpoint"
3 passed, 70 deselected in 0.47s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1110 passed, 13 skipped in 25.50s
```
