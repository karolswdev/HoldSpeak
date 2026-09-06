# Evidence - HS-162-03

- **Story:** HS-162-03 - The model drafter (frozen router; marked language; fallback proven)
- **Status:** done
- **Date:** 2026-09-01

## Proof

### Captured run — 2026-09-01T22:57:11Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/story162-03-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 91589ecec17ae5ac784f046fd201171c0f9166e4

```text
=== leg 1: scoped suites (isolated HOME): drafter + schema + both phase143 censuses ===
........................................................................ [ 69%]
.........s.....................s                                         [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_project_updates_schema.py:541: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
102 passed, 2 skipped in 31.17s
=== leg 2: THE LIVE .43 LEG (real HOME, real LAN inference) ===
.                                                                        [100%]
1 passed in 14.01s
```
