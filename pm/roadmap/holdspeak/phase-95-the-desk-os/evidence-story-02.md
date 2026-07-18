# Evidence - HS-95-02

- **Story:** HS-95-02 - OS-grade windows
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T02:35:53Z

- **Command:** `bash -c npm --prefix web run test:web 2>&1 | tail -4 && uv run python scripts/desk_gl_walk.py windows`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 910f5c729909b076982848552601b283054dbc85

```text
      Tests  244 passed (244)
   Start at  20:35:53
   Duration  8.58s (transform 620ms, setup 1.19s, import 2.67s, tests 2.35s, environment 7.69s)

windows walk 1440: 3 windows, drag to {'x': 201, 'y': 189}, tray parks+restores, rect+maximize survive reload, reopen presents
windows walk 393: sheet form ok
```
