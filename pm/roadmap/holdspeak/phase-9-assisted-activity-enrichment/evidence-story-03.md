# HS-9-03 evidence — Firefox companion extension events

## Files shipped

- `holdspeak/activity_extension.py` (new) — the parser + ingester.
  - `EXTENSION_SOURCE_BROWSER = "firefox_ext"`.
  - `FORBIDDEN_FIELDS` is a frozenset of every field whose name
    implies sensitive content (cookies, body, page_body, html,
    form / form_data / form_values / fields / inputs, password,
    credentials, headers, screenshot, image, selection, clipboard,
    …). The parser hard-rejects an event whose payload contains
    *any* of those keys, regardless of value. The intent is the
    important signal — an extension that ships a `cookies` field
    at all is misconfigured.
  - URLs must be `http(s)`; `file://`, `about:`, `chrome://`,
    `javascript:`, `data:`, and `ftp://` are all rejected at the
    scheme check.
  - Events flagged `private` or `incognito` are rejected.
  - `visited_at` must parse via `datetime.fromisoformat` (with a
    cheap `Z` → `+00:00` shim so the extension can send standard
    `2026-04-29T20:30:00Z`).
  - `ingest_extension_events(db, raw_events)` returns an
    `IngestResult{accepted, rejected, project_rule_updates}`.
    Rejections are reported with their batch index + a stable
    short reason string. After a successful upsert pass it calls
    `db.apply_activity_project_rules()` so extension-sourced
    records get the same project mapping as history-imported
    records.
- `holdspeak/web_server.py`
  - New Pydantic `_ActivityExtensionEventsRequest{events: list[dict]}`.
  - New endpoint `POST /api/activity/extension/events` that calls
    `ingest_extension_events()` and returns
    `result.to_payload()`. Loopback-only in practice — the
    runtime binds to `127.0.0.1` by default.
- `extensions/firefox/` (new) — minimal WebExtension scaffold:
  `manifest.json` (manifest_version 2, gecko id, `tabs` +
  `activeTab` + `storage` permissions), `background.js`
  (tab-activation + load-complete listeners that build the
  minimal event and POST it; refuses incognito tabs and
  non-`http(s)` URLs *before* the runtime gets a chance to),
  `options.html` + `options.js` (one input — the runtime URL).
- `docs/FIREFOX_EXTENSION_GUIDE.md` (new) — what it does, what
  it intentionally doesn't do, the threat model, the manual
  load-as-temporary-add-on instructions, and the source layout.

## Tests

```
$ uv run pytest tests/unit/test_activity_extension.py \
                tests/integration/test_web_activity_api.py -q
…
65 passed in 2.03s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1242 passed, 13 skipped in 29.66s
```

`tests/unit/test_activity_extension.py` covers the parser
contract end-to-end:

- `test_parse_accepts_minimal_https_event`
- **parametrized** `test_parse_rejects_any_forbidden_field` — one
  case per entry in `FORBIDDEN_FIELDS`, so adding any new
  forbidden field to the frozenset auto-extends the test surface.
- `test_parse_rejects_private_or_incognito_events`
- **parametrized** `test_parse_rejects_non_http_schemes` —
  file://, ftp://, javascript:, about:, chrome://, data:.
- `test_parse_rejects_missing_url`
- `test_parse_rejects_bad_visited_at`
- `test_parse_handles_z_suffix_iso_timestamps`
- `test_ingest_creates_record_under_extension_source` — entity
  extraction kicks in (a GitHub PR URL becomes
  `entity_type=github_pull_request` automatically).
- `test_ingest_rejects_forbidden_fields_per_event` — one bad
  event in a batch does not poison the rest; rejected events are
  reported with their index.
- `test_ingest_does_not_persist_record_for_rejected_event` —
  rejection means *no* row is upserted.
- `test_ingest_applies_project_rules` — extension-sourced records
  pick up project mapping just like history-imported ones.

`tests/integration/test_web_activity_api.py` covers the HTTP
surface:

- `test_extension_events_endpoint_creates_records`
- `test_extension_events_rejects_sensitive_fields` — POSTing
  events with `cookies`, `form_data`, or `private: true` returns
  zero accepted, the right reasons, and leaves the DB empty.
- `test_extension_events_applies_project_rules`

## Acceptance criteria — how each is met

- **Extension events can be posted to localhost.** New
  `POST /api/activity/extension/events`. Locked down by
  `test_extension_events_endpoint_creates_records`.
- **Events create or merge activity records.** Ingestion goes
  through `db.upsert_activity_record(...)`, which is the same
  upsert path used by history imports — same dedupe, same
  entity extraction.
- **Project mapping applies to extension records.** After every
  successful batch the ingester calls
  `db.apply_activity_project_rules()`. Locked down by
  `test_extension_events_applies_project_rules` and
  `test_ingest_applies_project_rules`.
- **Tests prove private/page-body data is not accepted.** The
  parametrized `test_parse_rejects_any_forbidden_field` covers
  every entry in `FORBIDDEN_FIELDS`;
  `test_parse_rejects_private_or_incognito_events` covers the
  private-browsing flags; the integration test
  `test_extension_events_rejects_sensitive_fields` proves the
  HTTP surface enforces the same rejections and leaves the DB
  unchanged.

## Threat-model notes (also in the dev guide)

- The runtime binds to `127.0.0.1` by default; the endpoint is
  loopback-only in practice.
- The extension is loaded as a temporary add-on (developer flow)
  and removed on browser restart. There is no addons.mozilla.org
  distribution path in this story.
- The extension itself never builds forbidden fields. The
  parser's `FORBIDDEN_FIELDS` set is defense-in-depth in case
  the extension is later modified.
