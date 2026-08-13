# Evidence - HS-131-13

- **Story:** HS-131-13 - Residual services take the admitted door
- **Status:** done
- **Date:** 2026-08-12

## Proof

### Captured run — 2026-08-13T04:28:14Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/home TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/tmp XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/home/.config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/home/.local/share XDG_CACHE_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/home/.cache .venv/bin/python -m pytest -q tests/unit/test_one_path_census.py tests/unit/test_one_path_context.py tests/unit/test_one_path_spine.py tests/unit/test_one_path_cardinality.py tests/unit/test_one_path_provenance.py tests/unit/test_residual_service_admission.py tests/integration/test_presence_learning_aftercare_broadcasts.py tests/unit/test_run_artifacts.py tests/unit/test_run_frames.py --basetemp=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13113-evidence/pytest -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 958df09bcbdb49a8b3d8cac4c746ea385b48e60d

```text
........................................................................ [ 42%]
........................................................................ [ 84%]
...........................                                              [100%]
171 passed in 44.79s
```

## Verification narrative

### What shipped

- **Cadence is admitted at request time.** `CadenceService.get_loop` retains the
  authenticated transport principal, opens one `cadence.next-action-draft`
  parent, freezes placement into schema-v57 deployment revision state before
  child admission, invokes the generic runner through one `inference.invoke`
  child per physical attempt, and stages the draft through the shared projection
  protocol. Missing authentication, disabled LLM support, unavailable placement,
  refusal, failure, cancellation, and off-contract output all fail closed to the
  deterministic action without constructing an engine outside the runner.
- **The exact local model is real, not receipt-only.** The `this_machine` factory
  now constructs `MeetingIntel(provider="local", model_path=<frozen revision>)`
  directly from immutable revision fields. It never re-reads mutable meeting
  config after admission, and a revision with no frozen path refuses
  `inference_local_deployment_model_unknown` before engine construction.
- **Cancellation wins publication.** An outer request-task cancellation durably
  cancels the Cadence parent, signals/fences its live child, re-raises
  `CancelledError`, and leaves late stages unpublishable. Tests cover cancellation
  while the provider is blocked and after the stage is already durable; recovery
  ends `DISCARDED`, never `PUBLISHED`.
- **Deletion before invention.** The duplicate Decisions route model seam,
  dormant `DeliveryService.prepare_pr_review`, and `build_intel_for_target` are
  deleted with no compatibility shim. The existing admitted Decision and
  Delivery services remain the sole paths. `LEGACY_UNCONTEXTUAL` now appears only
  in the separately chartered HS-131-16 mesh finding.
- **The kernel stays domain-blind.** Cadence prompt construction and validation
  remain in the Cadence domain; the generic runner learned no Cadence branch.

### Fence result

The executable census is now 134 sites: 68 allowlist sites, 24 admitted-seam
sites, 38 pinned findings in eight families, and **zero unregistered**. Relative
to the HS-131-10 checkpoint, this story removes ten finding pins and the retired
factory's last non-finding site: 145→134 total, 48→38 findings, 11→8 families.
No service, route, or other product surface entered the adapter allowlist. The
updated exact ledger is
[`assets/hs-131-10/findings-inventory.md`](./assets/hs-131-10/findings-inventory.md).

### Hostile counsel

The first independent pass returned **DO NOT RATIFY** and reproduced two real
product defects: frozen model A could execute mutable-config model B, and outer
request cancellation could leave a failed parent whose late stage recovery
published. Both were repaired with production-path regressions. The fresh pass
reran the original reproductions and returned:

```text
RATIFY FOR STORY CLOSE
```

The full report is
[`assets/hs-131-13/hostile-verdict.md`](./assets/hs-131-13/hostile-verdict.md).

### Official gate accounting

The final official two-lane gate ran on a quiet tree under isolated scratch
`HOME`, `TMPDIR`, XDG roots, pytest basetemp, and the explicit installed
Playwright browser cache. Its inherited-red totals were:

```text
67 failed, 4918 passed, 8 skipped in 178.76s
9 failed, 240 passed, 36 skipped, 16 deselected, 14 errors in 681.76s
```

The 90 normalized names were mechanically diffed against the HS-131-10
91-name baseline: **zero new names, one repaired** —
`test_a_failed_local_entry_admits_a_second_child_naming_the_cloud_revision`.
The red suite is not described as green; its inherited ledger remains explicit.
Full accounting is in
[`assets/hs-131-13/verification-summary.md`](./assets/hs-131-13/verification-summary.md).

### Discarded runs

One gate attempt was harness-truncated during lane 1 and produced no terminal
result. A later attempt overlapped PM inventory edits and therefore was not a
quiet-tree proof. Both are explicitly discarded and support no story claim.
