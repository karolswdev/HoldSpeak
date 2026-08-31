# Evidence - HS-158-06

- **Story:** HS-158-06 - The close (gates, suite amendments, final summary)
- **Status:** done
- **Date:** 2026-08-31

## Proof

### Captured run — 2026-08-31T19:51:47Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/close-158.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3703555230a0ecda27ad7df86545ca1fd0b02047

```text
== FULL SUITE:
12 failed, 7968 passed, 54 skipped in 1307.40s (0:21:47)
== SWEEP vs main baseline (run 33412916883 @ 6a5bd3e4, 26 names):
FAILED tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]
FAILED tests/unit/test_decision_record_service.py::test_promotion_cancellation_after_provider_return_never_publishes_artifact
branch-new-count=2
== FLAKE CANDIDATES RE-RUN LIVE:
..                                                                       [100%]
2 passed in 9.48s
== WEB GATES (recorded):
/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/web-check-out2.txt:bundle gate passed (Desk JS 1246160 B; Desk CSS 286962 B; source maps 0)
/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/web-baseline-out2.txt:Suite totals: 1862 passed, 1 failed, 0 skipped
/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/web-baseline-out2.txt:VERDICT: BRANCH-NEW FAILURES: 1
```
