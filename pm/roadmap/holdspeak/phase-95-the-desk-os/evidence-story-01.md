# Evidence - HS-95-01

- **Story:** HS-95-01 - The WebGL stage
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T02:19:27Z

- **Command:** `bash -c npm --prefix web run test:web 2>&1 | tail -4 && uv run python scripts/desk_gl_walk.py smoke && uv run python scripts/desk_gl_walk.py storm && echo '--- storm report ---' && cat uat/_runs/hs-95-01-walk/storm-report.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bebc376643e5abbe8ff8a404dfe5401561835293

```text
      Tests  234 passed (234)
   Start at  20:19:28
   Duration  8.24s (transform 642ms, setup 1.18s, import 2.48s, tests 2.20s, environment 7.41s)

smoke: tap-open ok, drag ok (330px), lasso bar=1, zone drag 307px
storm: {"gpu": "hardware", "frames": 962, "median_ms": 8.3, "p95_ms": 9.9, "max_ms": 10.3, "layout_events": 1, "paint_events": 2}
--- storm report ---
{
  "gpu": "hardware",
  "frames": 962,
  "median_ms": 8.3,
  "p95_ms": 9.9,
  "max_ms": 10.3,
  "layout_events": 1,
  "paint_events": 2
}
```
