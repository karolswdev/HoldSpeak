# HS-131-12 backend failure-name diff

**Date:** 2026-08-15

## Final command

```bash
env HOME=<fresh-home> \
  XDG_CONFIG_HOME=<fresh-home>/.config \
  XDG_DATA_HOME=<fresh-home>/.local/share \
  TMPDIR=<fresh-temp> \
  PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
  uv run pytest -q --tb=no --ignore=tests/e2e/test_metal.py
```

The complete compact output is the `2026-08-15T17:46:25Z` capture in
[evidence-story-12](../../evidence-story-12.md). Sol read every line before the
done decision.

## Result

```text
71 failed, 5543 passed, 44 skipped, 17 errors in 1468.06s (0:24:28)
```

The backend suite remains inherited-red and is not represented as green. The
result is classified by normalized pytest test name against the pinned
[HS-130-10 inherited ledger](../../../phase-130-one-truth/assets/hs-130-10/inherited-fails.txt):

| Set | Names |
|---|---:|
| HS-130-10 baseline | 102 |
| HS-131-12 final | 88 |
| Shared | 87 |
| Baseline-only | 15 |
| Current-only | 1 |

Normalization keeps only `FAILED tests/...` and `ERROR tests/...` names; order
and failure bodies do not affect the comparison.

## Current-only classification

The sole current-only name is:

```text
tests/uat/test_induction_integration_43.py::test_mesh_node_lifecycle
```

This test predates Phase 131 (`df5648a1`, 2026-07-09). The complete diagnostic
from the first readable run says the real `.43` UAT worker named `uat-worker`
was not live within 40 seconds and had `last_seen_seconds: None`. The already-
baselined `tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged`
failed in the same run for the same absent worker. This is a live-UAT environment
failure, not a Phase-131 product regression.

## Repaired current regressions

The first complete run exposed two additional names that were not in HS-130-10:

- `tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay`
  created a private node credential fixture with permissive filesystem mode. The
  fixture now uses `0600`; the focused real-hub test passes.
- `tests/unit/test_inference_kernel.py::test_tool_effect_is_causally_linked_child_with_own_receipt`
  embedded the machine's long absolute temporary path in a bounded kernel result
  reference. It now uses the stable filename; the focused test passes.

Neither name appears in the final 88-name set. The seven Phase-131-assigned sync
checks pass together with the real-hub regression (**8 passed**). The three
`test_live_bus.py` names remain inherited `ERROR` names in the full matrix, while
the repaired current selectors pass all three tests in the focused Chromium run
(**3 passed**).

## Environmental retry

The `2026-08-15T17:12:28Z` capture is not used for comparison: the filesystem
filled during that attempt, pytest reported `No space left on device`, and the
evidence output was truncated. Session-owned completed test homes were removed,
12 GiB of free space was established, and the full command was rerun from fresh
`HOME` and `TMPDIR` directories. The final capture completed through 100% with an
intact summary and failure-name list.

## Decision

The normalized final ledger contains **zero Phase-131 regressions**. The only
current-only name is an older live-worker UAT environment dependency; concrete
local regressions found by the full gate are repaired and independently green.
