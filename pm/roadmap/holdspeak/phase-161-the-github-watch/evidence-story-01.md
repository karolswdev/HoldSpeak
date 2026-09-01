# Evidence - HS-161-01

- **Story:** HS-161-01 - The provider adapter (real auth status, discovery, typed fallback, egress receipts)
- **Status:** done
- **Date:** 2026-09-01

## Proof

### Captured run — 2026-09-01T07:25:01Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/story161-01-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 58048c84cd9a73e8cc62411475c2d5417de84698

```text
=== leg 1: scoped suites (isolated HOME; two main-baseline kernel-broker names deselected) ===
.......................................ss............................... [ 43%]
........................................................................ [ 87%]
.....................                                                    [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
=== leg 2: live probe (real HOME, real gh) ===
..                                                                       [100%]
2 passed in 2.64s
```
