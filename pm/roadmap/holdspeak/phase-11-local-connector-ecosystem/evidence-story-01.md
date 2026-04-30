# HS-11-01 evidence — Connector manifest and SDK shape

## Files shipped

- `holdspeak/connector_sdk.py` (new) — the contract.
  - `ConnectorManifest` (frozen dataclass): id, label, version,
    kind, capabilities, description, requires_cli,
    requires_network, permissions, source_boundary, dry_run.
    Round-trips through `to_payload()` so manifests can persist
    as JSON.
  - `validate_manifest(raw) → ConnectorManifest` that **collects
    every problem** before raising, so authors fix them all at
    once. Each problem is a `ManifestError(field, code, message)`
    with a stable `code` string the SDK consumer can switch on.
  - Frozen vocabulary sets:
    - `KNOWN_KINDS`: `cli_enrichment`, `candidate_inference`,
      `extension_events`, `history_import` — covers everything
      phase 9 actually shipped.
    - `KNOWN_CAPABILITIES`: `records`, `annotations`,
      `candidates`, `commands`.
    - `KNOWN_PERMISSIONS`: read/write on each phase-9 table,
      plus `shell:exec`, `fs:read`, `loopback:http`, and the
      explicit-trust `network:outbound`.
    - `NETWORK_PERMISSIONS`: the subset that actually opens
      sockets. `requires_network=true` demands at least one of
      these in the declared permissions; otherwise validation
      fails with `network_permission_required`.
  - SDK Protocols (runtime-checkable): `Discover`, `Preview`,
    `Enrich`, `Clear`. Connector packs implement only the
    methods that match their manifest capabilities; `isinstance`
    works as expected.

## Tests

```
$ uv run pytest tests/unit/test_connector_sdk.py -q
…
27 passed in 0.03s
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1269 passed, 13 skipped in 29.73s
```

`tests/unit/test_connector_sdk.py` covers the validation contract:

- `test_validate_manifest_round_trips_a_well_formed_manifest`
- `test_validate_manifest_returns_immutable_dataclass`
- `test_validate_manifest_rejects_non_object_root`
- **parametrized** `test_validate_manifest_rejects_malformed_ids`
  — empty, leading digit, caps, spaces, too long.
- **parametrized** `test_validate_manifest_rejects_malformed_versions`
  — empty, missing patch, `v` prefix, four parts, `+build`,
  `latest`.
- `test_validate_manifest_rejects_unknown_kind`
- `test_validate_manifest_rejects_empty_capabilities`
- `test_validate_manifest_rejects_unknown_capability`
- `test_validate_manifest_requires_cli_when_kind_is_cli_enrichment`
- `test_validate_manifest_requires_network_perm_when_requires_network_true`
- `test_validate_manifest_accepts_loopback_only_extension_pack`
- `test_validate_manifest_rejects_unknown_permission`
- `test_validate_manifest_collects_every_error_at_once` —
  *eight different rule violations in one raw manifest, all
  reported together.*
- `test_validate_manifest_default_dry_run_is_true`
- `test_validate_manifest_dry_run_must_be_bool`
- `test_known_constants_match_phase_9_shape` — the kinds /
  capabilities cover what phase 9 actually shipped, so the
  later phase-11 stories can rebuild gh / jira / calendar /
  firefox_ext on top of this contract without surface drift.
- `test_sdk_protocols_are_runtime_checkable`
- `test_partial_implementations_are_partial_isinstance` — a
  preview-only pack is a `Preview`, not an `Enrich`.

## How acceptance criteria are met

- **Connector manifest schema is documented and validated.**
  The schema is the dataclass + validator in
  `holdspeak/connector_sdk.py`; the source comments document
  every field; `validate_manifest` enforces it.
- **SDK interfaces map cleanly to Phase 9 connector state/output
  tables.** The four Protocols correspond to the four flows phase 9
  actually shipped (discover work entities, preview a plan,
  enrich/import, clear scoped output). `KNOWN_CAPABILITIES`
  enumerates the existing output surfaces (`activity_records`,
  `activity_annotations`, `activity_meeting_candidates`, plus
  command plans).
- **Permission declarations are required for network-capable
  connectors.** Validated by
  `test_validate_manifest_requires_network_perm_when_requires_network_true`:
  setting `requires_network=true` without a network permission
  fails with `network_permission_required`.
- **Invalid manifests fail with actionable errors.** Every
  `ManifestError` has a stable `code` plus a human-readable
  `message` that names the offending field. The exception's
  string form is the joined error list.
- **Unit tests cover validation.** 27 tests, all green;
  parametrized cases over IDs, versions, and protocol coverage
  ensure regressions are caught at the lowest level.

## Notes

- This story deliberately ships only the *shape*. Phase-11
  stories HS-11-02..06 will:
  - HS-11-02: build a fixture-driven dry-run harness on top of
    the `Preview` Protocol.
  - HS-11-03..05: re-author the existing first-party connectors
    (`firefox_ext`, `gh`, `jira`) as ConnectorManifest + concrete
    classes that satisfy the Protocols.
  - HS-11-06: developer-facing docs (CONNECTOR_DEVELOPMENT.md).
- No remote distribution mechanism; no third-party package
  loading; no OAuth. Those are explicit phase-scope exclusions.
