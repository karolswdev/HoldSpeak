# Evidence - HS-96-06

- **Story:** HS-96-06 - Docs and the mechanical lock
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:33:09Z

- **Command:** `bash -c 
uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_design_system_guard.py 2>&1 | tail -1
echo '--- contributor path names the locks ---'
grep -c 'tokens:gate\|DESIGN_SYSTEM.md' web/README.md docs/internal/ARCHITECTURE_WEB_FRONTEND.md
(cd web && npm run check 2>&1 | tail -1)
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0bf64106b0906d5274e42a984388bdc6737b7fe7

```text
22 passed in 0.23s
--- contributor path names the locks ---
web/README.md:2
docs/internal/ARCHITECTURE_WEB_FRONTEND.md:2
✓ built in 3.13s
```
