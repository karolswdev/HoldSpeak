# HS-131-13 verification summary

**Date:** 2026-08-12
**Disposition:** **RATIFY FOR STORY CLOSE.**

## Focused admission proof

The orchestrator ran the one-path census, context, spine, cardinality,
provenance, and residual-service suites under scratch-resident isolated
`HOME`, `TMPDIR`, XDG roots, and pytest `--basetemp`:

```text
153 passed in 39.14s
```

Raw output: [`focused-tests.txt`](./focused-tests.txt).

The final executable census printed:

```text
one-path census: 134 sites
{'gateway': 1, 'witness-mint': 2, 'gateway-binding': 1,
 'allowlist': 68, 'seam': 24, 'finding': 38, 'unregistered': 0}
gateway_scopes=2 allowlist_scopes=55 seam_scopes=15 finding_families=8
```

This is the intended reduction from the HS-131-10 checkpoint: 145→134 sites,
48→38 findings, 11→8 families, still zero unregistered execution. Nothing was
moved onto a product-surface allowlist.

## Hostile verification

The first independent Terra pass found two real defects:

1. the `this_machine` branch froze model A but could construct mutable-config
   model B after admission;
2. cancelling the outer Cadence task closed its parent failed, allowing the
   provider thread's late staged output to publish during recovery.

Both were repaired structurally. Exact local construction now uses only the
frozen revision's model path and refuses `inference_local_deployment_model_unknown`
when it has none. `asyncio.CancelledError` durably cancels the Cadence parent,
signals/fences the live child, and re-raises; both before-stage and after-stage
race orderings end with no publication.

The fresh fix-round verdict is:

```text
RATIFY FOR STORY CLOSE
```

Full report: [`hostile-verdict.md`](./hostile-verdict.md).

## Gate repairs before the final run

The first complete official gate exposed five deterministic test-rig failures.
All five still installed their fake at the retired mutable-config factory, so
the new exact-revision constructor correctly bypassed the fake and tried to
load a real model. The assertions and product behavior were sound; the injection
boundary was stale. The three affected files were migrated without changing
assertions:

- two deferred-intel aftercare tests;
- one run-artifact test;
- two run-frame tests.

They passed 18/18 together after repair. A wider sweep reported 171 focused
passes, and the implementation agent's modified-rig sweep reported 2044 passes.
The unrelated mesh UAT name from that preliminary gate passed two of three serial
reproductions and did not recur in the final gate.

Two non-final runs are explicitly discarded:

- one harness-truncated run stopped during lane 1 with no terminal result;
- one run overlapped PM inventory edits and therefore was not a quiet-tree proof.

Neither supports the story judgment.

## Official full-suite gate — quiet tree

Command, under scratch-resident isolated `HOME`, `TMPDIR`, XDG roots, pytest
`--basetemp`, and explicit owner-installed Playwright browser cache:

```text
sh scripts/test_gate.sh
```

The two lanes reported:

```text
67 failed, 4918 passed, 8 skipped in 178.76s
9 failed, 240 passed, 36 skipped, 16 deselected, 14 errors in 681.76s
```

The red suite remains inherited and is not described as green. The normalized
failure ledger contains **90 names**; the HS-131-10 checkpoint baseline contains
**91**. Mechanical diff:

```text
new: 0
repaired: 1
  tests/unit/test_meeting_session_admission.py::
    test_a_failed_local_entry_admits_a_second_child_naming_the_cloud_revision
```

Artifacts: [`gate-failures.txt`](./gate-failures.txt) and
[`gate-diff.txt`](./gate-diff.txt).

**Full-suite judgment:** zero new failure names, one repaired; no HS-131-13
product regression remains.
