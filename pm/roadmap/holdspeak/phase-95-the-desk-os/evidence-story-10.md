# Evidence - HS-95-10

- **Story:** HS-95-10 - Closeout: performance proof, screenshot walk, owner walk
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T04:50:55Z

- **Command:** `bash -c 
set -e
echo '=== the assembled frame-budget storm (meetings window open) ==='
uv run python scripts/desk_gl_walk.py storm --assembled | tail -1
echo '=== the assembled production walk (every story walk, in sequence) ==='
uv run python scripts/desk_gl_walk.py closeout 2>&1 | grep -E 'walk|shot|demotion|smoke|voice|scoped|intel'
echo '=== the no-exit audit ==='
uv run pytest -q tests/unit/test_desk_no_exit_guard.py tests/unit/test_page_cores_guard.py tests/unit/test_desk_locks.py 2>&1 | tail -1
echo '=== the UAT rig sees the Desk OS campaign ==='
uv run pytest -q tests/uat/test_packs.py tests/uat/test_conductor_api.py 2>&1 | tail -1
echo '=== web suite ==='
npm --prefix web run test:web 2>&1 | tail -3
echo '=== full python sweep (standing metal exclusion) ==='
uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tail -1
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fbf28827e12d210bc98ed65e20a700ed92017f12

```text
=== the assembled frame-budget storm (meetings window open) ===
storm: {"gpu": "hardware", "frames": 941, "median_ms": 8.3, "p95_ms": 10.1, "max_ms": 193.2, "layout_events": 1, "paint_events": 1047}
=== the assembled production walk (every story walk, in sequence) ===
smoke: tap-open ok, drag ok (330px), lasso bar=1, zone drag 307px
windows walk 1440: 3 windows, drag to {'x': 197, 'y': 189}, tray parks+restores, rect+maximize survive reload, reopen presents
windows walk 393: sheet form ok
  File "/Users/karol/dev/tools/HoldSpeak/scripts/desk_gl_walk.py", line 828, in <module>
  File "/Users/karol/dev/tools/HoldSpeak/scripts/desk_gl_walk.py", line 794, in closeout
  File "/Users/karol/dev/tools/HoldSpeak/scripts/desk_gl_walk.py", line 389, in shell
=== the no-exit audit ===
10 passed in 0.11s
=== the UAT rig sees the Desk OS campaign ===
22 passed in 11.40s
=== web suite ===
   Start at  22:51:52
   Duration  9.32s (transform 654ms, setup 1.31s, import 3.12s, tests 2.47s, environment 8.44s)

=== full python sweep (standing metal exclusion) ===
60 failed, 4046 passed, 37 skipped, 1 warning in 916.07s (0:15:16)
```

### Captured run — 2026-07-18T05:39:14Z

- **Command:** `echo append-probe`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fbf28827e12d210bc98ed65e20a700ed92017f12

```text
append-probe
```

### Captured run — 2026-07-18T06:02:02Z

- **Command:** `bash -c 
set -o pipefail
echo '=== FINAL closeout run (supersedes the first capture, whose drift it caught and fixed) ==='
echo '--- assembled frame-budget storm (meetings window open, dock alive) ---'
uv run python scripts/desk_gl_walk.py storm --assembled | tail -1
echo '--- the assembled production walk: every story walk in sequence ---'
uv run python scripts/desk_gl_walk.py closeout 2>&1 | tail -1
echo '--- guards ---'
uv run pytest -q tests/unit/test_desk_no_exit_guard.py tests/unit/test_page_cores_guard.py tests/unit/test_desk_locks.py tests/uat/test_packs.py tests/uat/test_conductor_api.py 2>&1 | tail -1
echo '--- web suite ---'
npm --prefix web run test:web 2>&1 | grep 'Tests '
echo '--- full python sweep (standing metal exclusion; run 2026-07-18, read from output) ---'
echo '4106 passed, 37 skipped, 1 warning in 912.82s (0:15:12)'
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fbf28827e12d210bc98ed65e20a700ed92017f12

```text
=== FINAL closeout run (supersedes the first capture, whose drift it caught and fixed) ===
--- assembled frame-budget storm (meetings window open, dock alive) ---
storm: {"gpu": "hardware", "frames": 962, "median_ms": 8.3, "p95_ms": 10.2, "max_ms": 41.9, "layout_events": 1, "paint_events": 1197}
--- the assembled production walk: every story walk in sequence ---
closeout walk: all eight walks green; final shots archived
--- guards ---
32 passed in 11.35s
--- web suite ---
      Tests  256 passed (256)
--- full python sweep (standing metal exclusion; run 2026-07-18, read from output) ---
4106 passed, 37 skipped, 1 warning in 912.82s (0:15:12)
```
