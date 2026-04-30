# HS-13-01 evidence — Pack-driven runtime registry

## What shipped

- `holdspeak/connector_packs/calendar_activity.py` — new fourth
  first-party pack. Manifest: id `calendar_activity`, kind
  `candidate_inference`, capabilities `["candidates"]`,
  `requires_cli=None`, `requires_network=False`. Permissions:
  `read:activity_records`, `write:activity_meeting_candidates`.
  Re-exports `CALENDAR_DOMAINS` as `RECOGNIZED_DOMAINS` for the
  pack's source-boundary contract.
- `holdspeak/connector_packs/__init__.py` — `ALL_PACKS` now
  `(firefox_ext, github_cli, jira_cli, calendar_activity)`.
- `holdspeak/activity_connectors.py` — full rewrite. The
  hand-written `KNOWN_CONNECTORS` tuple is replaced by a
  derivation from `ALL_PACKS`:
  ```
  KNOWN_CONNECTORS = tuple(
      _descriptor_from_manifest(pack.MANIFEST) for pack in ALL_PACKS
  )
  ```
  `ConnectorDescriptor` is preserved as a frozen dataclass —
  every existing consumer reads through it — but its fields are
  now sourced from the underlying `ConnectorManifest` (carried
  on the descriptor as `.manifest`). The `capabilities` field
  is filtered to row-producing capabilities
  (`{"records", "annotations", "candidates"}`) so the manifest's
  `"commands"` capability (a dry-run preview surface, not a
  table) doesn't leak into the descriptor — keeping the API +
  fixture shapes byte-stable.
- `holdspeak/activity_connectors.py` adds an
  `enrichment_descriptors()` helper. The registry now contains
  all four packs (records-ingesters + enrichment connectors);
  the activity-enrichment API filters through this helper so it
  surfaces only `kind in {cli_enrichment, candidate_inference}`
  — i.e. the same three connectors as before
  (`gh`, `jira`, `calendar_activity`).
- `holdspeak/web_server.py` — `/api/activity/enrichment/connectors`
  switched from iterating `KNOWN_CONNECTORS` to
  `enrichment_descriptors()`. Payload shape unchanged.

## Acceptance criteria

- [x] `connector_packs/` ships four pack modules (`firefox_ext`,
  `github_cli`, `jira_cli`, `calendar_activity`).
- [x] `activity_connectors.KNOWN_CONNECTORS` is derived from
  `connector_packs.ALL_PACKS`; the static tuple of
  `ConnectorDescriptor(...)` literals is gone.
- [x] `GET /api/activity/enrichment/connectors` returns the same
  payload shape as before, sourced from pack manifests via
  `enrichment_descriptors()`.
- [x] Existing phase-9 tests stay green without modification.
  Phase-11 `test_connector_packs.py` had its `len(ALL_PACKS)`
  assertion bumped from 3 → 4 to reflect the new fourth pack
  module — every other phase-11 assertion is untouched.
- [x] No code path references both `ConnectorDescriptor` and
  `ConnectorManifest` for the same connector — the descriptor
  carries its source manifest on `.manifest`, so callers
  needing manifest fields (permissions, version, source
  boundary) reach them through one object.

## Tests ran

```
$ uv run pytest -q tests/unit/test_connector_packs.py \
    tests/unit/test_activity_connector_preview.py \
    tests/unit/test_connector_fixture_harness.py \
    tests/integration/test_web_activity_api.py
.....................................................................   [100%]
69 passed in 2.47s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1308 passed, 13 skipped in 32.30s
```

The 13 skipped tests are pre-existing skips (mock meeting WAV
not committed, llama-cpp / Qwen GGUF model not installed) and
unrelated to this story.

## New unit tests

- `test_calendar_pack_manifest_shape` — locks the calendar
  pack's manifest fields, including the absence of shell /
  network permissions.
- `test_calendar_pack_recognized_domains_match_extractor` —
  `RECOGNIZED_DOMAINS` mirrors `activity_candidates.CALENDAR_DOMAINS`;
  drift would mean the pack documents a domain set the
  extractor doesn't recognise.
- `test_registry_is_derived_from_all_packs` — `KNOWN_CONNECTORS`
  contains exactly four descriptors with ids
  `{firefox_ext, gh, jira, calendar_activity}`, and each
  descriptor's `.manifest.id` equals its `.id` (the derivation
  is correct).

## Why the descriptor survives

Phase 13 bins for "delete the descriptor entirely" were on the
table, but every consumer (the API endpoint, the dry-run
harness, the fixture runner) reads through a small descriptor
surface (`id` / `label` / `kind` / `capabilities` /
`requires_cli` / `description` / `cli_status()`). Keeping the
descriptor as a thin wrapper kept this story to a registry-
derivation change with zero behaviour drift; HS-13-02..05 will
build on the same surface without further plumbing churn.

## Greenfield

No migrations, no shims. The pack-derived registry simply
replaces the hand-written tuple. Greenfield discipline holds.
