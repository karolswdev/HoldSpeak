# Evidence - HS-162-01

- **Story:** HS-162-01 - The update ledger (schema v70 + repo + revision pinning)
- **Status:** done
- **Date:** 2026-09-01

## Proof

### Captured run — 2026-09-01T22:18:45Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/story162-01-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c5862710137951098241ebf1ff1675b5188ca71c

```text
=== leg 1: scoped schema/repo/fence suites (isolated HOME) ===
........................s.................................s............. [ 64%]
s......................s................                                 [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_project_updates_schema.py:541: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_delta_schema.py:636: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:489: Owner's real DB not found (CI or isolated HOME)
108 passed, 4 skipped in 30.08s
=== leg 2: real-DB reconcile (real HOME, COPY of the owner DB) ===
.                                                                        [100%]
1 passed in 0.59s
```
