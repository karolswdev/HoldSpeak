# Evidence - HS-175-05

- **Story:** HS-175-05 - The week brief (Monday brief window widened to the calendar week; calendar + meeting collectors)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:41:43Z

- **Command:** `bash -c HOME=$(mktemp -d) /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_hs175_week_brief.py tests/unit/test_monday_brief_service.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7ab36239e347fa719ac03458fb627a25ab37af36

```text
..............................                                           [100%]
30 passed in 8.87s
```
