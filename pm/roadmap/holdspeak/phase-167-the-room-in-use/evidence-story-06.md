# Evidence - HS-167-06

- **Story:** HS-167-06 - The Tuesday walk (the owner's first project on his real desk, attended — OWNER VERDICT)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T23:40:59Z

- **Command:** `bash -c echo REAL-DESK-RUN-TRANSCRIPT; python3 -c "import json;t=json.load(open(\"pm/roadmap/holdspeak/phase-167-the-room-in-use/assets/story-06-walk/real-1440/walk167-transcript.json\"));s=t.get(\"steps\") or t;print(\"steps\",len(s));[print(x.get(\"step\"),\"ms=\",x.get(\"elapsed_ms\")) for x in s]"; sqlite3 $HOME/.local/share/holdspeak/holdspeak.db "select id,lifecycle from projects"; echo WALK-FIXES-UNIT; HOME_REAL=$HOME; export HOME=$(mktemp -d); uv run pytest -q tests/unit/test_hs167_walk_fixes.py tests/unit/test_hs167_debts.py -p no:cacheprovider 2>&1 | tail -1; echo RUNNER-ISOLATED-1440; export HOME=$HOME_REAL; HS167_WALK=1 HS167_WALK_DB=isolated PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright uv run pytest -q "tests/e2e/live167_walk.py::test_tuesday_walk[1440]" -p no:cacheprovider 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 063d853b258cc4606926ed96d560a94a7552d471

```text
REAL-DESK-RUN-TRANSCRIPT
steps 8
step1_interview ms= 728
step2_github_connection ms= 1295
step3_jira_connection ms= 5559
step4_activate ms= 4095
step5_room ms= 2908
step6_real_change ms= 31713
step7_steward ms= 15413
step8_update ms= 4413
proj-102233e71c47|archived
WALK-FIXES-UNIT
20 passed in 3.99s
RUNNER-ISOLATED-1440
1 passed in 79.94s (0:01:19)
```
