# Evidence - HS-163-01

- **Story:** HS-163-01 - The run ledger (schema v71: policy/run/step/command persistence; STW-001)
- **Status:** done
- **Date:** 2026-09-01

## Proof

### Captured run — 2026-09-02T04:46:01Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/737d97f2-738a-46f5-b6e1-8d3d7fec615e/scratchpad/story163-01-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 33aa2448cfaacf32d0a80a550391078119870b40

```text
=== LEG 1: isolated-HOME scoped (steward schema + db + fences) ===
.................................................................s...    [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_project_updates_schema.py:572: Owner's real DB not found (CI or isolated HOME)
140 passed, 1 skipped in 37.96s
=== LEG 2: real-HOME real-DB reconcile on a COPY (v71 incl. steward tables) ===
.                                                                        [100%]
1 passed, 29 deselected in 0.59s
LEG1_EXIT=0 LEG2_EXIT=0
```
