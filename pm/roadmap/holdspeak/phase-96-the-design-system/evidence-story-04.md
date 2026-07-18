# Evidence - HS-96-04

- **Story:** HS-96-04 - One material grammar
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:28:52Z

- **Command:** `bash -c 
(cd web && node scripts/validate-tokens.cjs && node scripts/generate-tokens.cjs --check)
echo '--- the one material (no per-window recipes remain) ---'
(grep -n 'rgba(14, 12, 19' web/src/desk/desk.css || echo 'zero per-window fill recipes')
grep -c 'desk-window-radius\|desk-window-shadow\|desk-window-blur' web/src/desk/desk.css
echo '--- storm with the glass family-wide ---'
uv run python scripts/desk_gl_walk.py storm --assembled | tail -1
npm --prefix web run test:web 2>&1 | grep 'Tests '
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8998dfd3c5425d1d32a6bedf4db65c3812458cf0

```text
token gate: clean (69 allow-listed exceptions, all in use)
tokens.css and tokens.gen.ts match design-tokens.json
--- the one material (no per-window recipes remain) ---
zero per-window fill recipes
4
--- storm with the glass family-wide ---
storm: {"gpu": "hardware", "frames": 961, "median_ms": 8.3, "p95_ms": 10.1, "max_ms": 10.4, "layout_events": 1, "paint_events": 824}
      Tests  256 passed (256)
```
