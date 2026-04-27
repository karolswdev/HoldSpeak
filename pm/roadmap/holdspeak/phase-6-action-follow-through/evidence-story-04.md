# HS-6-04 Evidence - Artifact/Action Detail Linking

## Shipped Result

HS-6-04 connects action items and artifacts back to source meeting
context:

- Global action-item cards now include an Open Meeting action.
- Project action-item cards now include an Open Meeting action.
- Project artifact cards now include an Open Meeting action.
- Opening a meeting now also loads that meeting's artifacts from
  `/api/meetings/{id}/artifacts`.
- Selected meeting detail now renders an Artifacts panel with confidence,
  creation time, source count, and body text.

This uses existing `meeting_id` relationships and the existing meeting
artifacts API. It does not introduce a new cross-linking schema.

## Files

- `holdspeak/static/history.html`
  - adds `selectedMeetingArtifacts`.
  - loads artifacts when `openMeeting(id)` runs.
  - adds Open Meeting actions to action-item and project-artifact cards.
  - renders selected meeting artifacts in the detail pane.
- `tests/integration/test_web_server.py`
  - pins the browser wiring for selected meeting artifacts and source
    meeting links in the history UI smoke test.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems or meeting_artifacts"
5 passed, 67 deselected in 0.49s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py
114 passed in 2.13s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1107 passed, 13 skipped in 22.15s
```
