# HS-7-02 Evidence - Saved Meeting Export API

## Shipped Result

HS-7-02 adds a local saved-meeting handoff export endpoint:

- `GET /api/meetings/{meeting_id}/export?format=markdown`
- `GET /api/meetings/{meeting_id}/export?format=json`

The endpoint uses the shared HS-7-01 renderer, includes synthesized
artifacts where available, returns download-friendly content disposition
headers, rejects unsupported formats, and does not write to arbitrary
filesystem paths or publish externally.

## Files

- `holdspeak/web_server.py`
  - adds `/api/meetings/{meeting_id}/export`.
  - maps `md` to `markdown`.
  - returns `text/markdown` or `application/json`.
  - includes artifacts from `db.list_artifacts()`.
- `tests/integration/test_web_server.py`
  - covers Markdown export content and headers.
  - covers JSON artifact payload.
  - covers invalid format and missing meeting responses.

## Verification

```text
uv run pytest -q tests/integration/test_web_server.py -k "meeting_export_endpoint or meeting_artifacts"
2 passed, 71 deselected in 0.51s
```

```text
uv run pytest -q tests/integration/test_web_server.py tests/unit/test_meeting_exports.py
79 passed in 1.74s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1110 passed, 13 skipped in 22.62s
```
