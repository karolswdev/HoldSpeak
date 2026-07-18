# Evidence - HS-95-07

- **Story:** HS-95-07 - Configuration through the desk
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T03:51:30Z

- **Command:** `bash -c npm --prefix web run test:web 2>&1 | tail -3 && uv run python scripts/desk_gl_walk.py config && echo '--- desk config-route link sweep ---' && (grep -rn 'to={workroomHref("/settings"\|to={workroomHref("/profiles"\|to="/setup"\|to="/profiles"' web/src/desk/ --include='*.tsx' || echo 'zero desk links to configuration routes')`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62b2370aeceec892f0ca37e47f295f343255e237

```text
   Start at  21:51:30
   Duration  9.82s (transform 737ms, setup 1.36s, import 3.32s, tests 2.56s, environment 8.72s)

config walk: settings change round-trips + persists; runs-on/cadence/integrations open in-world; flat routes live
--- desk config-route link sweep ---
zero desk links to configuration routes
```
