# Web-inherited failure baseline

The file `tests/web-inherited-baseline.txt` lists vitest test
identifiers that fail on main (inherited debt, not regressions).
The checker `scripts/check_web_baseline.py` diffs a live run's
failures against this list and speaks the sweep vocabulary.

## Running the checker

```bash
# Execute vitest and check:
uv run python scripts/check_web_baseline.py --run

# Or consume an existing vitest JSON results file:
uv run python scripts/check_web_baseline.py path/to/results.json
```

Exit 0 when zero branch-new failures. Exit 1 when any branch-new
failure exists.

## Vocabulary

| Term | Meaning |
|---|---|
| BASELINE-MATCHED | A failure present in the baseline (inherited) |
| BRANCH-NEW | A failure NOT in the baseline (regression) |
| HEALED | A baseline entry that now passes |
| baseline-subset/exact, zero branch-new | All failures are inherited; no regressions |

## Adding an entry

An entry may be added ONLY when:
1. The test file is byte-identical to main (`git diff main -- <file>`
   produces empty output).
2. The provenance comment names the phase that verified byte-identity
   and, when known, the originating story (e.g., HS-132-05).

## Removing an entry

Remove an entry ONLY when the failure has healed. The removal commit
message must name the healing commit or the fix that resolved it.

## Flaky tests

A test that FLAPS (fails some full-suite runs, passes serially) is
NOT inherited debt and never enters this baseline — baselining a
flake hides a real reliability defect. Protocol: serial ×2 green →
name it in the flake families (the phase status/handover ledger);
recurrence beyond = DIAGNOSE. First member caught by this checker's
own second run: ModelLibraryCore "keeps radio selection inert,
restores Add focus…" (focus-timing shape, serial 7/7 ×2 green,
2026-08-29).
