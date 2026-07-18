# Evidence - HS-95-05

- **Story:** HS-95-05 - Dictation through the desk
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T03:04:20Z

- **Command:** `bash -c npm --prefix web run test:web 2>&1 | tail -3 && uv run python scripts/desk_gl_walk.py dictation && echo '--- desk /dictation link sweep ---' && (grep -rn 'to={workroomHref("/dictation"' web/src/desk/ --include='*.tsx' || echo 'zero desk links to /dictation')`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b9b3d25d7c77eb3b8f7d3eac369efb7e91ea4753

```text
   Start at  21:04:20
   Duration  9.26s (transform 656ms, setup 1.28s, import 2.97s, tests 2.56s, environment 8.20s)

voice landed in-world: 'Hello world from the desk. Hello world from the desk.'
scoped in-world: '⌁ About Untitled meeting'
dictation walk: chip + pullout open in-world; voice lands; flat route lives
--- desk /dictation link sweep ---
zero desk links to /dictation
```
