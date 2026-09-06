# Evidence - HS-168-03

- **Story:** HS-168-03 - The Connections face (Settings → Connections; one state, one verb per tool; the sign-in fold; glass rig at both widths)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-04T04:25:13Z

- **Command:** `bash -c cd web && npx vitest run src/pages/cores 2>&1 | grep -E 'Tests|Test Files'; cd .. && HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_api_surface.py tests/e2e/test_hs168_connections_glass.py -k 'not real_readiness' 2>&1 | tail -1; uv run pytest -q -p no:cacheprovider tests/e2e/test_hs168_connections_glass.py -k real_readiness 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 92da91f5993b8b6398ef268e62c3baba66392e6b

```text
 Test Files  26 passed (26)
      Tests  190 passed (190)
9 passed, 2 deselected in 21.85s
2 passed, 4 deselected in 18.77s
```
