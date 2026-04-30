# HS-9-13 evidence — Connector dry-run harness

## Files shipped

- `holdspeak/activity_connector_preview.py` (new) — the shared
  harness. Exposes `ConnectorDryRunResult` (frozen dataclass with
  `to_payload()`), an `UnknownConnectorError`, and a single
  `dry_run(db, connector_id, *, limit)` entry point that
  dispatches to the right preview helper:
  - `gh` → `preview_github_cli_enrichment` → `commands` +
    `proposed_annotations` (one per command).
  - `jira` → `preview_jira_cli_enrichment` → same shape.
  - `calendar_activity` → `preview_calendar_meeting_candidates`
    → `proposed_candidates`.
  Mutation-free by construction: the harness only calls `db.list_*`
  and connector-side `preview_*` helpers; it never invokes any
  `*_run_*` helper. Each section is capped at
  `PAYLOAD_SECTION_CAP = 100` and the result flags `truncated`
  when any cap fires.
- `holdspeak/web_server.py` — new endpoint
  `GET /api/activity/enrichment/connectors/{id}/dry-run?limit=…`
  that calls `dry_run()` and returns `{"dry_run": result.to_payload()}`.
  Unknown ids → 404.
- `web/src/pages/activity.astro`
  - Imports `CommandPreview` and renders one hidden instance so
    the scoped `.cmd` CSS + the document-wide `[data-cmd-copy]`
    delegator are bundled with the page (same trick `/dictation`
    uses).
  - New scoped CSS for `.dry-run-output`, `.dry-section`,
    `.dry-list`, `.dry-list-item`, `.dry-note`, `.dry-note--warn`.
- `web/src/scripts/activity-app.js`
  - Each connector card now renders a "Dry-run" button alongside
    Enable/Disable, plus a `<div data-dry-run-output>` (initially
    hidden) below the meta row.
  - `renderDryRun(connectorId, payload)` emits permission notes
    (`warn` tone), warnings (neutral tone), one `<figure class="cmd cmd--{tone}">`
    per planned command (so the document-wide copy delegator works
    on them out of the box), a "Proposed annotations" list when
    present, and a "Proposed candidates" list when present.
  - Click handler on `[data-dry-run]` calls the new endpoint and
    feeds the response into the renderer.

## Tests

```
$ uv run pytest tests/unit/test_activity_connector_preview.py \
                tests/integration/test_web_activity_api.py -q
…
27 passed in 1.88s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1198 passed, 13 skipped in 28.29s
```

Six new unit tests in
`tests/unit/test_activity_connector_preview.py`:

| Test | What it locks down |
|---|---|
| `test_dry_run_unknown_connector_raises` | `dry_run()` rejects ids that aren't registered. |
| `test_dry_run_gh_returns_uniform_payload_shape` | Every key the API contract names is present, types are right, and disabled-by-default surfaces a permission note. |
| `test_dry_run_calendar_emits_proposed_candidates` | Calendar connector emits only candidates (no commands / annotations); `cli_required` / `cli_available` are `None`. |
| `test_dry_run_does_not_mutate_db` | Annotation + candidate row counts unchanged after running every connector's dry-run. |
| `test_dry_run_warns_when_no_relevant_activity` | Empty ledger → friendly per-connector warning, not an exception. |
| `test_dry_run_disabled_connector_still_returns_a_plan` | Plan is still computed; permission_notes carry the "disabled" reason — the whole point of dry-run. |

Three new integration tests in
`tests/integration/test_web_activity_api.py`:

| Test | What it locks down |
|---|---|
| `test_connector_dry_run_returns_uniform_shape_per_connector` | Same payload shape across all three connectors via the API. |
| `test_connector_dry_run_does_not_mutate_db` | API path is mutation-free even with seeded github / calendar records. |
| `test_connector_dry_run_unknown_connector_returns_404` | Unknown ids reject at the HTTP layer. |

## How acceptance criteria are met

- **Dry-run API returns structured preview results.** `GET
  /api/activity/enrichment/connectors/{id}/dry-run` returns the
  uniform `dry_run` payload (`connector_id`, `kind`, `capabilities`,
  `enabled`, `cli_required`, `cli_available`, `commands`,
  `proposed_annotations`, `proposed_candidates`, `warnings`,
  `permission_notes`, `truncated`).
- **Dry-run results include warnings and permission notes.** The
  harness adds permission notes when the connector is disabled or
  the required CLI is missing, and warnings when the ledger has
  no relevant activity for that connector.
- **Dry-run never writes records, annotations, or candidates.**
  Locked down by both `test_dry_run_does_not_mutate_db`
  (unit, direct DB) and `test_connector_dry_run_does_not_mutate_db`
  (integration, through the HTTP layer).
- **Connectors can reuse the same preview response shape.**
  `ConnectorDryRunResult.to_payload()` is the only shape the
  endpoint produces. Phase 11 connector packs only need to plug
  into the dispatcher in `dry_run()`.
- **Tests prove DB state is unchanged after dry-run.** See above.

## Notes

The browser side renders commands through the `cmd` markup that
`CommandPreview` already controls — no new copy logic, no new
component — so the dry-run preview matches the rest of the system
(`/dictation` dry-run trace, design gallery, etc.). Permission
notes and warnings stack above the cmd block so the user reads
*"why this won't currently run"* before they start scanning the
plan itself.
