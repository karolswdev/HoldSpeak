# HS-11-03 evidence — Firefox companion connector pack

## Files shipped

- `holdspeak/connector_packs/__init__.py` (new) — registers
  `ALL_PACKS` as the canonical-order tuple of pack modules.
- `holdspeak/connector_packs/firefox_ext.py` (new) — exports a
  `MANIFEST: ConnectorManifest` that re-validates at import
  time, plus `CAPTURED_FIELDS` (re-export of
  `activity_extension.ALLOWED_FIELDS`) and `REJECTED_FIELDS`
  (re-export of `FORBIDDEN_FIELDS`).

## Manifest declaration

```
id:          firefox_ext
kind:        extension_events
capabilities: ["records"]
requires_cli: null
requires_network: true
permissions: ["loopback:http", "write:activity_records"]
source_boundary: "Loopback POSTs from a local Firefox WebExtension. …"
dry_run:     true
```

## How acceptance criteria are met

- **Firefox connector pack can be installed locally for
  development.** Pack ships alongside the existing
  `extensions/firefox/` WebExtension scaffold + the
  `docs/FIREFOX_EXTENSION_GUIDE.md` install guide (HS-9-03).
  The pack's `source_boundary` documents that the extension is
  a temporary add-on with no extension-store distribution path.
- **Events are accepted only through loopback.**
  `requires_network: true` plus `permissions: ["loopback:http"]`
  declares this in the manifest. The runtime endpoint
  (`/api/activity/extension/events`, HS-9-03) binds to
  127.0.0.1 by default; the pack manifest matches the runtime's
  actual binding.
- **Manifest declares captured fields and permissions.** The
  pack module exports `CAPTURED_FIELDS` mirroring
  `activity_extension.ALLOWED_FIELDS`, and `REJECTED_FIELDS`
  mirroring `FORBIDDEN_FIELDS`. The drift test
  (`test_firefox_pack_captured_fields_match_parser`) makes any
  future divergence fail at unit-test time.
- **Fixture tests cover accepted and rejected payloads.** The
  HS-9-03 unit suite (`tests/unit/test_activity_extension.py`)
  parametrizes 39 cases over every entry in
  `FORBIDDEN_FIELDS` and every blocked URL scheme. The pack
  re-exports those frozensets so the manifest layer documents
  exactly the contract the parser already enforces.

## Tests

```
$ uv run pytest tests/unit/test_connector_packs.py -q -k firefox
…
4 passed in 0.04s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1305 passed, 13 skipped in 29.56s
```
