# HS-9-12 evidence — Connector controls and output deletion

## Files shipped

- `holdspeak/activity_connectors.py` (new) — small registry of known
  activity-enrichment connectors. Each `ConnectorDescriptor` carries
  `id`, `label`, `kind` (`cli_enrichment` | `candidate_inference`),
  `capabilities` (`("annotations",)` for `gh`/`jira`,
  `("candidates",)` for `calendar_activity`), an optional
  `requires_cli`, and a one-line description. The registry is
  intentionally static for phase 9; phase 11 generalizes it via
  manifest-driven connector packs.
- `holdspeak/activity_candidates.py` — extracted `CALENDAR_CONNECTOR_ID`
  to a module-level constant so the registry can refer to it
  without re-stating the literal `"calendar_activity"` string.
- `holdspeak/web_server.py` —
  - `GET /api/activity/enrichment/connectors` now iterates
    `KNOWN_CONNECTORS`, returns one entry per connector with
    `label`, `kind`, `capabilities`, `requires_cli`, `description`,
    and a `cli_status` block when the connector requires a CLI.
    `gh`/`jira`'s legacy top-level `github`/`jira` fields are kept
    for the existing preview/run flow.
  - `PUT /api/activity/enrichment/connectors/{id}` now validates
    against `KNOWN_CONNECTOR_IDS` (no longer hard-coded to gh/jira).
  - `DELETE /api/activity/enrichment/connectors/{id}/annotations`
    (new) — clears `activity_annotations` rows authored by that
    connector. 404 for unknown ids; 400 if the connector's
    capabilities don't include `annotations`.
  - `DELETE /api/activity/enrichment/connectors/{id}/candidates`
    (new) — symmetric clear for `activity_meeting_candidates`.
- `web/src/pages/activity.astro` — new "Connectors" panel
  rendered between Project rules and Meeting candidates. Empty
  scaffold (`#connectors`, `#connectors-message`) plus scoped
  styles for `.connector-card`, `.connector-head`,
  `.connector-actions`, `.connector-error`. Uses the shared `Pill`
  tones for enabled/disabled and CLI ready/missing.
- `web/src/scripts/activity-app.js`
  - Adds the connector list to the parallel `load()` fetch.
  - `renderConnectors()` — emits one `<article class="connector-card">`
    per connector with: title + monospace id + enabled/disabled
    pill + CLI-ready/missing pill (when applicable), description,
    capabilities + last_run + CLI path, an error block when
    `last_error` is set, an Enable/Disable button, and per-
    capability "Clear annotations" / "Clear candidates" buttons.
  - Delegated click handler on `#connectors`:
    - Toggle button issues `PUT /api/activity/enrichment/connectors/{id}`.
    - Clear-annotations / clear-candidates each open a
      `holdspeakConfirm` with explicit scope copy ("Issues and PRs
      on GitHub are unchanged.", etc.) before calling the
      connector-scoped `DELETE` endpoint.

## Tests

```
$ uv run pytest tests/integration/test_web_activity_api.py -q
…
18 passed in 1.51s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1189 passed, 13 skipped in 30.45s
```

Five new tests in `tests/integration/test_web_activity_api.py`:

| Test | What it locks down |
|---|---|
| `test_connector_list_includes_calendar_with_capabilities` | All three known connectors surface; capabilities + kind + requires_cli + cli_status fields are present and correctly populated. |
| `test_clear_connector_annotations_deletes_only_that_connectors_output` | Clearing `gh` annotations leaves `jira` annotations intact. |
| `test_clear_connector_candidates_deletes_only_that_connectors_output` | Calendar candidates clear via the connector-scoped DELETE. |
| `test_clear_connector_unknown_connector_returns_404` | Unknown ids reject. |
| `test_clear_connector_capability_mismatch_returns_400` | "Clear candidates" on `gh` rejects (it produces only annotations); "Clear annotations" on `calendar_activity` rejects (it produces only candidates). |

The existing `test_activity_page_serves_browser_surface` was extended
with three new assertions: the `#connectors` and
`#connectors-message` containers and the
`/api/activity/enrichment/connectors` URL all show up in the bundled
JS chunk.

## Acceptance criteria — how each is met

- **`/activity` shows known connector states.** The new Connectors
  panel renders one card per registered connector. Each card shows
  enabled/disabled, last run, last error, capabilities, and CLI
  availability where relevant.
- **User can enable or disable a connector.** Enable/Disable
  button on each card calls `PUT /api/activity/enrichment/connectors/{id}`
  with `{enabled: !current}`. The list reloads on success and the
  pill flips.
- **User can clear connector-created annotations.** "Clear
  annotations" button → `holdspeakConfirm` (with the canonical
  "source data is untouched" scope language) → `DELETE
  /api/activity/enrichment/connectors/{id}/annotations`.
- **User can clear connector-created meeting candidates.** Same
  flow against the `/candidates` endpoint. Calendar candidates
  expose this path; `gh`/`jira` cards do not (their capabilities
  don't include `candidates`, so the button isn't rendered).
- **Last-run errors are visible.** When `last_error` is set on
  the connector state, the card adds the `.has-error` class
  (red border) and renders `<p class="connector-error" role="alert">`
  with the error text.
- **No connector can run invisibly.** The existing `gh`/`jira`
  run endpoints already enforce `connector.enabled` server-side
  (verified by `test_github_enrichment_run_requires_explicit_enablement`).
  The new UI surfaces enablement directly so users can't be
  surprised by a connector that quietly turned itself on.

## Notes on scope

This story is presentation + scoped-deletion only. The Firefox
companion extension (`HS-9-03`), the connector dry-run harness
(`HS-9-13`), and the phase exit (`HS-9-06`) remain backlog. The
new panel is structured so those stories can plug into the same
card grammar (e.g. a "Dry-run" button alongside Enable/Disable).
