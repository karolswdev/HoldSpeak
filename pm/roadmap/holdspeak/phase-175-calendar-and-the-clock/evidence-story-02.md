# Evidence - HS-175-02

- **Story:** HS-175-02 - Calendar events on the desk (the week view, the next seam, events as material)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:40:40Z

- **Command:** `bash -c HOME=$(mktemp -d) /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_hs175_calendar_wire.py tests/unit/test_api_surface.py tests/unit/test_db_schema_policy.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e219ed27d38d772e6bcd41043b42db8af427a16b

```text
...............................                                          [100%]
31 passed in 10.18s
```
