# Evidence - HS-131-01

- **Story:** HS-131-01 - Frozen deployment revisions and one sync registry
- **Status:** done
- **Date:** 2026-08-09

## Proof

### Captured run — 2026-08-09T22:09:33Z

- **Command:** `sh -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_primitive_contract.py tests/unit/test_web_routes_sync.py tests/unit/test_inference_kernel.py tests/unit/test_deployment_revisions.py -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3679b49cb278223fc875dcededf9d0cddcbdcf1c

```text
............................                                             [100%]
28 passed in 3.42s
```

## Full-suite regression diff (orchestrator-run, read before flip)

Baseline: pinned worktree at the charter commit `eaebaee3`, isolated HOME,
`pytest -q --deselect tests/e2e/test_metal.py` → **84 failed, 4707 passed,
17 errors**. Story tree, same command and isolation → **78 failed, 4729
passed, 17 errors**. Failure-name diff (see `assets/hs-131-01/`):

- **NEW: none.** Zero regression names against baseline.
- **REPAIRED: exactly the six HS-130-10 sync-contract failures assigned to
  this story** — `test_source_identity_must_be_a_known_qualified_kind`,
  `test_pull_body_validates_against_changeset_envelope`,
  `test_schemas_cover_exactly_sync_kinds`,
  `test_swift_sync_kind_matches_hub` (retired for the stricter
  `test_python_web_sync_contract_is_complete`, rationale in its docstring),
  `test_pull_serializes_meetings_and_artifacts`,
  `test_push_live_merges_meeting_and_keeps_audit_inbox`.
- The seventh 131-owned failure (`test_ipad_synced_graph_workflow_runs_on_the_hub`)
  remains with HS-131-04 as chartered.
- Mid-verification the first implementation pass introduced 8 new failure
  names (3 schema-version pins from the v43→v44 bump, 5 engine-construction
  behavior regressions from the revision-based constructor). All 8 were
  repaired before this flip; the final run above is the repaired tree.
- `test_source_identity_returns_the_receipt_to_the_desk_subject` still fails
  and is the re-ledgered inherited failure (94-bucket), unchanged from baseline.

## Acceptance criteria verification

- Immutable content-addressed revisions: `holdspeak/deployment_revisions.py`,
  `deployment_revisions` table (schema v44), capture/resolve proven in
  `tests/unit/test_deployment_revisions.py` (mutation + deletion after capture
  leave endpoint/model/secret-slot unchanged; engine constructs post-delete).
- No mutable profile re-read: `build_intel_for_target` no longer calls
  `db.profiles.get()`; `build_intel_for_revision` feeds only frozen revision
  values into the pure `build_meeting_intel_for_profile` builder.
- One registry: `SYNC_REGISTRY` in `holdspeak/services/sync_service.py`
  derives kinds, buckets, schemas, merger availability, pull serialization,
  and qualified-kind validation; pull/push iterate the registry.
- Revision sync round-trip resolves on the receiving DB; push rejects
  credential-bearing values; only the `secret_slot` identifier crosses.
- No Swift source changed.
