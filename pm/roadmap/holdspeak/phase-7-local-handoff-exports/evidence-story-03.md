# HS-7-03 Evidence - Browser Handoff Export Action

## Shipped Result

HS-7-03 adds browser controls in selected meeting detail for local
handoff exports:

- `Local Markdown` downloads the Markdown handoff export.
- `Local JSON` downloads the JSON handoff export.
- Both controls call the local HS-7-02 endpoint and do not publish to
  external systems.

## Files

- `holdspeak/static/history.html`
  - adds selected meeting export buttons.
  - adds `downloadSelectedMeetingExport(format)`.
  - uses `/api/meetings/{meeting_id}/export?format=...`.
- `tests/integration/test_web_server.py`
  - pins browser wiring for both export controls and the local API path.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or meeting_export_endpoint"
3 passed, 70 deselected in 0.53s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/unit/test_meeting_exports.py
79 passed in 1.75s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1110 passed, 13 skipped in 22.20s
```
