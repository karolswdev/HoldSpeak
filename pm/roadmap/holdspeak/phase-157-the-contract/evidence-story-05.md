# Evidence - HS-157-05

- **Story:** HS-157-05 - The close (gates, suite updates, final summary)
- **Status:** done
- **Date:** 2026-08-31

## Proof

### Captured run — 2026-08-31T15:21:39Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/close-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9cc1d6fd90e00ead192702b3fbb7ebc858a74eca

```text
== FULL SUITE (recorded 2026-08-31T09:19): ==
12 failed, 7766 passed, 53 skipped in 1243.10s (0:20:43)
== NAME-DIFF vs main CI baseline (run 33373358100, 26 names):
== local failures:       12
== main baseline:       26
== BRANCH-NEW (local, not in main baseline):
FAILED tests/e2e/test_hs143_assignments_glass.py::test_assignments_overview_real_hub[error-1440]
FAILED tests/unit/test_scheduled_recording_conductor.py::test_one_shot_disables_after_cancelled
== WEB GATES (recorded):
/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/web-check-out.txt:bundle gate passed (Desk JS 1245914 B; Desk CSS 286962 B; source maps 0)
/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/web-baseline-out.txt:VERDICT: baseline-subset, zero branch-new
== BRANCH-NEW CANDIDATES RE-RUN IN ISOLATION (live):
..                                                                       [100%]
2 passed in 3.79s
== PHASE SUITES (live, post fence-N-1):
..................................................................       [100%]
282 passed in 27.62s
```
