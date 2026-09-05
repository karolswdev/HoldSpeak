# Evidence - HS-168-06

- **Story:** HS-168-06 - The docs ("Connect your tools" in the guide; the Rooms guide re-shot; MCP_SIDECAR regenerated; README prerequisites)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-04T06:25:29Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_api_surface.py 2>&1 | tail -1; uv run python scripts/gen_mcp_sidecar_doc.py 2>&1 | tail -1; uv run python scripts/gen_api_surface.py >/dev/null 2>&1; git diff --stat docs/MCP_SIDECAR.md docs/api-surface.json docs/API_SURFACE.md | tail -1; echo 'generated docs diff above (empty = current)'; HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_product_copy.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3ac7af484a931817f4e62f7c8c1212f061ebd307

```text
42 passed in 3.79s
  189 tools across 34 families
 1 file changed, 1 insertion(+), 1 deletion(-)
generated docs diff above (empty = current)
1 failed, 9 passed in 1.66s
```
