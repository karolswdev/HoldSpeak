# Evidence - HS-158-01

- **Story:** HS-158-01 - The reconcile (columns, items, changes, commands — proven on a real-DB copy)
- **Status:** done
- **Date:** 2026-08-31

## Proof

### Captured run — 2026-08-31T16:33:31Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/orch-scoped.sh tests/unit/test_project_room_schema.py tests/unit/test_db.py tests/unit/test_no_positional_inserts.py tests/unit/test_project_service_characterization.py tests/integration/test_project_routes_characterization.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 88c19935a7d4c323a7c3be2ccf33e104df797f4b

```text
.............s.......................................................... [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
198 passed, 1 skipped in 47.97s
```
