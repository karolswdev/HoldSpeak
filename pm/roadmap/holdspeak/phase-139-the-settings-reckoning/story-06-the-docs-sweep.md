# HS-139-06 — The docs sweep

- **Project:** holdspeak
- **Phase:** 139
- **Status:** done
- **Depends on:** 139-05
- **Unblocks:** 139-07
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

Entry-point docs reference dials that no longer exist or now live
elsewhere; stale docs would re-teach the old room.

## Scope

- **In:** sweep README.md, docs/USER_GUIDE (or equivalent entry docs),
  docs/SECURITY.md, and any doc the killed/moved dials are named in
  (grep the killed field names + module names); update the settings MCP
  tool descriptions if they enumerate keys; doc-drift and product-copy
  guards green.
- **Out:** new documentation features; internal phase docs.

## Acceptance criteria

- [ ] No entry-point doc references a killed or moved control in its old
  home; moved controls are documented at their new home.
- [ ] Doc-drift guard, product-copy guard, and api-surface manifest all
  green.

## Test plan

- **Unit:** tests/unit/test_doc_drift_guard.py, test_product_copy.py,
  test_api_surface.py.
