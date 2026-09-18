# Evidence - HS-200-12

- **Story:** HS-200-12 - Connect a real meeting to reviewed outcomes
- **Status:** done
- **Date:** 2026-09-17

## Proof

### Captured run — 2026-09-18T03:50:48Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.uu6TDW7c4d uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_action_owner_enforcer_plugin.py tests/unit/test_hs172_loop_wire.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a9a2164703162d06ad5ee45b4772f83788e2cde

```text
............................................................             [100%]
60 passed in 13.85s
```

### Captured run — 2026-09-18T03:51:03Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.5cuY1hZDhl PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -p no:cacheprovider tests/e2e/test_hs200_meeting_outcomes_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2a9a2164703162d06ad5ee45b4772f83788e2cde

```text
..                                                                       [100%]
2 passed in 33.65s
```

## Two reasons no real meeting ever produced a proposal (found here, confirmed by counsel on the pre-fix tree)

1. The HS-172 bridge read `dec["text"]`; `decision_capture` writes `{"decision": …}`. Every real decision was skipped.
2. `action_owner_enforcer` emitted `gap: "missing_both"` and an unregistered `gap_count` against a registry contract declaring `gap: boolean` in a closed object. Under the bound executor every real run of the action extractor failed typed-output validation, retried to the ceiling, and no action item ever became a proposal. Counsel's probe with the real validator: `OLD SHAPE REJECTED: … unregistered fields: ['gap_count']` / `NEW SHAPE: ACCEPTED`.

The audit's "the meeting flow ends in a row nobody reads" was, one layer down, "nothing ever produced the row". Both repaired; the real chain (`process_next_intel_job`, the bound plugin host, real plugins, the drainer HS-200-42 built) now yields 2 decisions + 3 actions from an imported transcript, each stamped job / attempt / extraction revision.

## What was built

Retry identity at the service: `retry_key = sha256(meeting | transcript revision | kind | span | ordinal)`, unique in every state; confirm and dismiss are conditional UPDATEs inside the chain transaction and replay their durable result; two racing confirms mint one chain. Each proposal carries its transcript span, extraction provenance and support (verbatim quote → SUPPORTED; anchored → LINKED; nothing → NO SOURCE). Typed unknowns (`OWNER · UNKNOWN`, `DUE · UNKNOWN`) stay unknown until the owner supplies them, and a supplied value reads `· SUPPLIED`. Edit in place drops support to `LINKED · EDITED` and keeps the record. The review face: one verb per row (`Confirm`), `Edit`/`Dismiss`/`Open evidence` in `MORE`, one filled primary (`Accept reviewed`, which confirms only SUPPORTED/LINKED rows with no unknowns and names what it left), `ALREADY KEPT n` a verb that opens the kept rows (the verdict, Q5), `ATTEMPT 2 · SAME JOB` on a resumed job, a `PRIOR REVISION` disclosure when an earlier transcript's decided rows exist. 13 additive columns on `follow_through_proposals`; the canonical schema snapshot regenerated through the test's own normaliser.

## Pre-fix failures (clean tip 7b0d5c3c)

```
E       AssertionError: assert 0 == 5            # the real chain produced nothing (gaps 1 and 2)
E       AssertionError: []  assert [] == ['decision', 'decision']
E       assert 3 == 2                            # a confirmed proposal re-minted on repeated completion
E       AssertionError: {'error': 'Proposal not found or already decided'}   # a retried confirm errored instead of replaying
6 failed, 4 deselected in 3.83s
```

## Counsel-on-built: RATIFY-WITH-CONDITIONS, all paid

P0: the schema snapshot fence was red (regenerated). P1: `Accept reviewed` bulk-confirmed unsupported rows (ruled and fenced: only SUPPORTED/LINKED without unknowns; `ACCEPTED 2 · LEFT 3 · UNSUPPORTED 1 · UNKNOWN 2`); the no-duplicate claim held per transcript revision only (the USER_GUIDE says so exactly; `PRIOR REVISION · n DECIDED` disclosure on the face); a supplied owner was indistinguishable from an extracted one (`SUPPLIED` token). P2: confirm on a deleted meeting returned 500 (now a named 409 `meeting_deleted`); the meeting's name was said twice, then at 393 zero times because the window chrome ellipsised the title to nothing (the title bar now carries the name at both widths and the wing strip drops beneath it at ≤480, a chrome fix older than this story); kept rows carry `Open`. Reported for the BACKLOG: two library raw buttons inside the ceiling (`Disclosure` trigger, `ProgressPlan` action); the 0.6 content-word support threshold reads a cross-turn decision as unsupported.

## Not verified

A real model route end to end (the sandbox cannot reach the LAN); one intermittent 393 glass failure whose text was lost, followed by four consecutive green runs; `Open evidence` landing on the scrolled transcript row was exercised in vitest only.
