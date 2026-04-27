# HS-7-01 Evidence - Handoff Export Renderer

## Shipped Result

HS-7-01 opens Phase 7 and updates the shared meeting export renderer for
local handoff workflows:

- Markdown action items now include due date, review state, and source
  timestamp when present.
- Markdown exports can include synthesized artifacts with title, type,
  status, confidence, source count, and body.
- JSON exports can include an `artifacts` array without wrapping or
  replacing the existing meeting-state payload shape.
- Existing callers remain compatible because artifact inclusion is an
  optional keyword argument.

## Files

- `holdspeak/meeting_exports.py`
  - adds optional `artifacts` support to `render_meeting_export()` and
    `write_meeting_export()`.
  - adds artifact serialization helpers for dicts and dataclass-like
    objects.
  - enriches Markdown action item rendering with review/provenance
    details.
- `tests/unit/test_meeting_exports.py`
  - covers action item review/provenance output.
  - covers artifact-aware Markdown export.
  - covers artifact-aware JSON export.
- `pm/roadmap/holdspeak/phase-7-local-handoff-exports/`
  - opens Phase 7 with local handoff export stories.

## Verification

```text
uv run pytest -q tests/unit/test_meeting_exports.py
6 passed in 0.25s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1109 passed, 13 skipped in 23.11s
```
