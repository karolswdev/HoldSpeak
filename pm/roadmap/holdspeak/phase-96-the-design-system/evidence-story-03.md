# Evidence - HS-96-03

- **Story:** HS-96-03 - Component state specs
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:25:18Z

- **Command:** `bash -c 
uv run pytest -q tests/unit/test_design_system_guard.py 2>&1 | tail -1
npm --prefix web run test:web 2>&1 | grep 'Tests '
uv run python scripts/desk_gl_walk.py focus
(cd web && npm run tokens:gate)
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3cc52275090f03d0d1b04eb8d27895ddfef48cb1

```text
4 passed in 0.04s
      Tests  256 passed (256)
focus walk: 14 tab stops, 14 wear the accent ring; e.g. ['Minimize Desk memory', 'Maximize Desk memory', 'Close Desk memory', 'INPUT', 'EverythingNeeds / runnin', 'Filter']

> holdspeak-web@0.0.1 tokens:gate
> node scripts/validate-tokens.cjs

token gate: clean (70 allow-listed exceptions, all in use)
```
