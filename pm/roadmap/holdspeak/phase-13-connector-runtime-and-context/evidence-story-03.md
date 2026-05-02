# HS-13-03 evidence — Pack-declared settings + defaults

## What shipped

- `holdspeak/connector_sdk.py`
  - New `SettingDescriptor(key, type, default, label, help)`
    dataclass and `SETTING_TYPES = {"int", "float", "bool",
    "str"}` constant.
  - `ConnectorManifest.settings_schema:
    tuple[SettingDescriptor, ...]` (defaults to `()`). Two
    helpers on the manifest: `setting_keys()` for the PUT
    validator, `setting_default(key)` for the runners.
  - `ConnectorManifest.to_payload()` now serialises
    `settings_schema` so the loader contract still round-trips.
  - `validate_manifest` parses settings_schema entries with
    full per-entry error reporting: bad `key` regex, unknown
    `type`, missing `default`, default-type mismatch (with
    explicit bool/int separation so a `type: int` default
    can't be `True`), duplicate keys, malformed list shape.
  - `resolve_setting(manifest, settings, key)` returns the
    user value when present and well-typed, otherwise the
    schema default. Bool values for `int`/`float` settings are
    rejected at the resolve layer too (defense-in-depth).
- `holdspeak/connector_packs/github_cli.py` — declares
  `settings_schema = [timeout_seconds (float), max_bytes (int),
  limit (int)]` with the legacy module-constant defaults so
  honest packs see byte-stable behaviour.
- `holdspeak/connector_packs/jira_cli.py` — same shape.
- `holdspeak/connector_packs/calendar_activity.py` — declares
  only `limit (int, default 50)`.
- `holdspeak/connector_packs/firefox_ext.py` — empty schema
  (the extension parser is the contract).
- `holdspeak/web_server.py`
  - `POST /api/activity/enrichment/github/run` and
    `/jira/run` resolve their tunables via
    `resolve_setting(pack.MANIFEST, connector.settings, key)`
    instead of the old `settings.get(key, hard_coded_default)`
    pattern. The pack manifest is now the only source of
    defaults.
  - `PUT /api/activity/enrichment/connectors/{id}` validates
    every key in `settings` against the descriptor's
    `manifest.setting_keys()`. Unknown keys → 400 with a
    message naming the offending keys + the allowed set, so a
    misconfigured client can fix the call without guessing.

## Acceptance criteria

- [x] `ConnectorManifest.settings_schema:
  tuple[SettingDescriptor, ...]` with `validate_manifest`
  enforcing well-formed entries. Verified:
  `tests/unit/test_connector_settings.py` —
  `test_well_formed_settings_schema_round_trips`,
  `test_malformed_settings_schema_entry_fails_validation` (six
  parametrised malformed entries),
  `test_duplicate_setting_keys_fail_validation`,
  `test_settings_schema_must_be_a_list`.
- [x] gh + jira packs declare timeout / max_bytes / limit;
  calendar declares limit; firefox_ext declares an empty
  schema. Verified: `test_github_pack_declares_runtime_tunables`,
  `test_jira_pack_declares_runtime_tunables`,
  `test_calendar_pack_declares_only_a_limit`,
  `test_firefox_pack_declares_an_empty_schema`.
- [x] `run_github_cli_enrichment` /
  `run_jira_cli_enrichment` resolve defaults via the pack
  schema, not module constants. Wired in
  `holdspeak/web_server.py` via `resolve_setting(MANIFEST,
  connector.settings, key)`. Verified: existing run-tests
  (`test_github_enrichment_run_requires_explicit_enablement`,
  jira analogue) pass byte-identically.
- [x] PUT `/api/activity/enrichment/connectors/{id}` rejects
  unknown setting keys with a 400 + readable error. Verified:
  `test_put_connector_settings_rejects_unknown_key`,
  `test_put_connector_settings_rejects_keys_on_empty_schema`.
- [x] Existing tests pass without changes to settings
  payloads. Verified: full sweep below — same prior-passing
  cases, +22 new from this story.
- [x] New unit tests cover schema validation, default
  resolution, unknown-key rejection. 17 new unit cases in
  `test_connector_settings.py` + 3 new integration cases in
  `test_web_activity_api.py`.

## Tests ran

```
$ uv run pytest -q tests/unit/test_connector_settings.py \
    tests/unit/test_connector_packs.py \
    tests/unit/test_activity_github.py \
    tests/unit/test_activity_jira.py \
    tests/unit/test_connector_runtime.py \
    tests/integration/test_web_activity_api.py
96 passed in 2.40s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1342 passed, 13 skipped in 33.08s
```

The pre-existing 13 skips (mock meeting WAV, llama-cpp / Qwen
GGUF) are unrelated. +22 over HS-13-02 reflects the new
schema/resolve unit cases plus the three PUT-validation
integration cases.

## Why bool ≠ int at every layer

Python's `bool` is a subclass of `int`, so a naive
`isinstance(value, int)` accepts `True`/`False`. That would
let a manifest declare `{"type": "int", "default": True}` or
let a user override a numeric setting with `true` and have
the runner read the value as `1`. The validator and
`resolve_setting` both treat them as distinct so a settings
dict carrying a stale boolean for a numeric key falls back to
the schema default rather than silently coercing.

## Why the runners stay greenfield

The pack-declared `DEFAULT_*` module constants sit alongside
the schema entries (each schema entry references the
constant). The constants are no longer read at runtime —
`resolve_setting` is — but they keep the literal default in
one named place per pack, which keeps the schema readable as
documentation. Phase 13 is greenfield (HoldSpeak isn't
released), so no settings-migration ceremony is needed for
existing connector rows; mismatched stale settings keys are
silently ignored at resolve time and a fresh PUT trims them
out.
