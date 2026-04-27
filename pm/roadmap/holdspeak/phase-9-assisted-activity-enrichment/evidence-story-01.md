# HS-9-01 Evidence - Connector Registry and Annotation Persistence

## Shipped Result

HS-9-01 opens Phase 9 and adds the local persistence substrate for
assisted activity enrichment.

The implementation adds:

- DB schema version 14
- `activity_enrichment_connectors`
- `activity_annotations`
- `ActivityEnrichmentConnectorState`
- `ActivityAnnotation`
- connector state create/update/list/run-result helpers
- annotation create/list/delete helpers
- activity-record reference validation
- JSON settings/value persistence
- confidence clamping for annotations

No connector runs, external commands, network calls, credential handling,
browser extension endpoints, or web controls were added in this slice.

## Verification

```text
uv run pytest -q tests/unit/test_db.py -k "activity_enrichment or activity_annotations"
3 passed, 55 deselected in 0.44s
```

```text
uv run pytest -q tests/unit/test_db.py
58 passed in 1.80s
```

```text
git diff --check
```
