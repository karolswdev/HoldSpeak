# Phase 79 — Backend Decomposition II — final summary

**CLOSED 2026-07-03, 6/6 stories, one day.** The Phase-63 discipline applied to the
next three backend monoliths. Behavior-preserving throughout: tests unmodified,
zero patch-target edits, route paths byte-identical, the manifest regen stable.

## The ledger

| File | Before | After |
|---|---|---|
| `db/activity.py` | 1,596 (one class, ~45 methods) | six concern mixins, largest 406; `__init__` 27 |
| `web/routes/system.py` | 1,299 (one builder, five families) | five routers + `_shared` 49, largest `settings.py` 701 (named budget); `__init__` 26 |
| `web/routes/primitives.py` | 1,294 (41 routes, one builder) | seven family routers + `_shared` 159, largest 333; `__init__` 36 |

Public surfaces unchanged: `ActivityRepository`, `build_system_router`,
`build_primitives_router`, and the pinned wire vocabulary
(`CANONICAL_SOURCE_TYPES` / `canonical_source_type`) all resolve exactly as before.

## Verbatim accounting (programmatic, per story)

Zero code-body lines differ across all three carves. The enumerated non-verbatim
lines are import plumbing only: distributed headers, ~72 lazy in-body relative
imports retargeted one package level deeper, one sibling
(`from .workflow_graph` → `from ..workflow_graph`), and the two public re-exports.
Two of those classes were caught by tests exactly as designed (the workflow-run
tests caught the sibling; the pinned-vocabulary test caught the missing re-export).

## The lock

The backend density guard now covers the three packages: `__init__` files
composition-only (≤ 90), concern modules ≤ 600, `system/settings.py` at a named
800 (one concern: the settings PUT validation matrix). Red-proven on a fabricated
601-line module. New named watch item: `db/core.py` (schema DDL + migrations,
snapshot-pinned).

## The closeout bars

- Full suite: **3,113 passed / 37 skipped** (`--ignore=tests/e2e/test_metal.py`).
  One run showed a single non-reproducing failure
  (`test_replay_after_target_correction_changes_routing`) that passed in isolation
  and on the full re-run — recorded as a flake candidate, not hidden.
- Web build: 17 pages, green. `swift test`: 425 passed (the iPad consumes the
  moved routes; paths byte-identical).
- Manifest: byte-stable on a fresh regen; the only diffs this phase were module
  fields (the Phase-72 accepted class), now per-submodule.
- Docs: the backend map covers both decomposition phases; the ARCHITECTURE
  diagram paths updated with the render guard green.
