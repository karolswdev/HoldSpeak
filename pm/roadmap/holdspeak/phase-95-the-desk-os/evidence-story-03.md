# Evidence - HS-95-03

- **Story:** HS-95-03 - The shell: dock, switching, layouts
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T02:48:03Z

- **Command:** `bash -c uv run pytest -q tests/unit/test_desk_locks.py tests/unit/test_web_null_read_guard.py 2>&1 | tail -1 && npm --prefix web run test:web 2>&1 | tail -3 && uv run python scripts/desk_gl_walk.py windows && uv run python scripts/desk_gl_walk.py shell`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 443ebe70e42cd63830783f7a598489fdeafe8e9f

```text
7 passed in 0.09s
   Start at  20:48:04
   Duration  9.06s (transform 681ms, setup 1.25s, import 2.98s, tests 2.56s, environment 7.96s)

windows walk 1440: 3 windows, drag to {'x': 198, 'y': 189}, tray parks+restores, rect+maximize survive reload, reopen presents
windows walk 393: sheet form ok
shell walk 1440: dock, snap, cycle, park/restore, close, reset, menu dispatch
```
