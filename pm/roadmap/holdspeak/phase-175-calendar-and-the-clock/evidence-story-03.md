# Evidence - HS-175-03

- **Story:** HS-175-03 - Event-born scheduled recordings (auto-create from calendar events with meeting URLs)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:40:53Z

- **Command:** `bash -c HOME=$(mktemp -d) /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_hs175_event_recordings.py tests/unit/test_no_positional_inserts.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0efd0c244cfd4675f7b8411c2abf7eb811014611

```text
..................                                                       [100%]
18 passed in 5.02s
```
