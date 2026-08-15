# HS-131-14 verification summary

**Date:** 2026-08-13
**Disposition:** **RATIFY FOR STORY CLOSE.**

## Focused plugin-admission proof

All verification used scratch-resident isolated `HOME`, `TMPDIR`, XDG roots, and pytest `--basetemp`.

Primary-tree hostile matrix:

```text
159 passed in 1.74s
```

Primary-tree wider plugin/one-path sweep:

```text
566 passed in 79.56s
```

Independent hostile verification reran the single-handle, timeout-election, all-fourteen-builtin, deferred/live, receipt/projection, segment-probe, context, cardinality, and census cases and returned:

```text
RATIFY
```

After repairing the one full-gate test-double regression, the captured final focused suite closed with:

```text
811 passed in 106.10s
```

## Executable fence

```text
one-path census: 105 sites
{'gateway': 1, 'witness-mint': 2, 'gateway-binding': 1,
 'allowlist': 70, 'seam': 25, 'finding': 6, 'unregistered': 0}
gateway_scopes=2 allowlist_scopes=56 seam_scopes=16 finding_families=6
```

Relative to HS-131-13, HS-131-14 removes all 30 `plugin-default-provider` findings and both `legacy-uncontextual-factory` findings: 134 -> 105 executable sites, 38 -> 6 findings, and 8 -> 6 families. Zero unregistered execution remains. No plugin builtin or segment-probe scope entered `ADAPTER_ALLOWLIST`; the one admitted `PluginDispatch.chat` consumer is classified as an admitted seam.

## Structural result

- Fourteen builtin plugins no longer construct or cache providers and no longer expose `intel_call` injection as a production bypass.
- `segment_probe` takes only an explicitly admitted dispatch handle; meeting startup no longer creates configured intelligence before session admission and currently remains lexical pending HS-131-17.
- One opaque `PluginDispatch` binds one runner-issued context, revision, destination, warrant basis, attempt ordinal, and cancellation signal to exactly one physical completion.
- Missing, forged, released, stale, cross-child, cancelled, incompatible, and over-cardinality handles refuse before physical work.
- Host timeout atomically revokes and classifies the handle: zero-claim timeout cannot later dispatch; already-claimed timeout is indeterminate and cannot publish.
- Provider failure reaches the child as failure, not a successful plugin error mapping. Compatibility retry is a separately admitted `_r2` child with its own handle/context/receipt; only the winner materializes.
- Deterministic plugins remain runnable with no inference child.
- The public `build_configured_meeting_intel` symbol is deleted; its private construction body is dominated by the exact context-validating entrance.

## Full-suite accounting

The final official two-lane gate ran on a quiet primary tree under isolated scratch `HOME`, `TMPDIR`, XDG roots, pytest basetemp, and the explicit installed Playwright browser cache. It completed both lanes and remained honestly red:

```text
67 failed, 5083 passed, 8 skipped in 176.76s
10 failed, 239 passed, 36 skipped, 16 deselected, 14 errors in 683.35s
```

Its 91 normalized names were mechanically compared with HS-131-13's 90-name ledger: 90 shared, one apparent new name, zero repaired. The apparent new name was:

```text
tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged
```

This is an inherited real-model canary flake, not a current-diff regression. The exact name appears in the HS-131-01, HS-131-02, HS-131-05, and HS-131-06 ledgers. The current tree failed two isolated repeats because the live `.43` model returned a successful mesh response without the requested `PYLON-CANARY-7` token. An untouched detached HS-131-13 control tree at `190b1bed` then passed once and failed once with the same missing-canary response. HS-131-14 changes neither the prompt nor the receiver path; HS-131-16 separately owns that pinned receiver family.

The first quiet gate also found one real HS-131-14 regression:

```text
tests/unit/test_fault_plane.py::test_named_plugin_fault_fails_exactly_that_key_then_exact_retry
```

The local host test double did not accept the new per-invocation `dispatch` keyword. It was repaired, passed alone, passed in the 274-test focused regression set, passed in the 811-test evidence capture, and is absent from the final gate ledger. The red suite is not described as green; exact accounting is in `gate-diff.txt` and `gate-failures.txt`.

## Discarded runs

- One gate was launched from the implementation agent's worktree because the shell's persistent cwd had been changed by worktree isolation. It reached lane-one output and was harness-killed before a terminal result. It is invalid for the primary tree and supports no claim.
- One primary-tree gate launch overlapped the tail of hostile verification and was deliberately stopped before interpretation to preserve the quiet-tree rule.
