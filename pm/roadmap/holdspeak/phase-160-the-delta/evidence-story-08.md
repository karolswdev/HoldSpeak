# Evidence - HS-160-08

- **Story:** HS-160-08 - The close (gates, suite amendments, final summary)
- **Status:** done
- **Date:** 2026-08-31

## Proof

### Captured run — 2026-09-01T04:34:48Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/close-160.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9e2244c8e1de47cbaa04563f7652e90dafb39449

```text
== AUTHORITATIVE SUITE:
12 failed, 8335 passed, 56 skipped in 1372.34s (0:22:52)
== SWEEP vs main (27 names @ 33459107466):
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
FAILED tests/unit/test_one_path_census.py::test_every_model_execution_site_is_in_exactly_one_bucket
== ROOT-CAUSE + CHURN PROOFS (live):
.......................................                                  [100%]
39 passed in 66.62s (0:01:06)
== WEB FINALS (recorded):
Suite totals: 2060 passed, 1 failed, 0 skipped
VERDICT: BRANCH-NEW FAILURES: 1
```
