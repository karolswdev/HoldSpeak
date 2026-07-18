# Evidence - HS-95-09

- **Story:** HS-95-09 - Docs: the Desk OS is the documented product
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T04:22:38Z

- **Command:** `bash -c uv run pytest -q tests/e2e/test_mermaid_renders.py tests/unit/test_doc_drift_guard.py tests/unit/test_product_copy.py 2>&1 | tail -1 && (cd web && npm run check 2>&1 | tail -2) && echo '--- demoted-route instruction sweep (docs) ---' && (grep -rnE 'go to the [A-Z][a-z]+ page|open the [A-Z][a-z]+ page|navigate to /(dictation|history|settings|live)' README.md docs/*.md || echo 'zero page-navigation instructions')`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** de39c50e05c762768b17b42573fe3335ebe513c3

```text
30 passed in 27.77s
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 3.28s
--- demoted-route instruction sweep (docs) ---
zero page-navigation instructions
```
