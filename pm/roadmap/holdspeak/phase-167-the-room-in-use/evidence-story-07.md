# Evidence - HS-167-07

- **Story:** HS-167-07 - The docs (the Rooms guide re-shot; the library contract; MCP_SIDECAR counts guarded; the dedicated docs story)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T23:43:08Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_doc_drift_guard.py tests/unit/test_docs*.py -p no:cacheprovider 2>&1 | tail -1; uv run python scripts/gen_mcp_sidecar_doc.py >/dev/null 2>&1; git diff --quiet docs/MCP_SIDECAR.md && echo GENERATOR-IDEMPOTENT || echo GENERATOR-CHANGED; ls docs/images/project-rooms 2>/dev/null | wc -l`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cdc8fc90fbc8adb9846fce73b5849fcb9ed4f30f

```text
no tests ran in 0.00s
GENERATOR-CHANGED
       0
```

### Captured run — 2026-09-03T23:43:53Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_doc_drift_guard.py $(ls tests/unit/test_roadmap_vocabulary*.py 2>/dev/null) -p no:cacheprovider 2>&1 | tail -1; A=$(shasum docs/MCP_SIDECAR.md | cut -c1-12); uv run python scripts/gen_mcp_sidecar_doc.py >/dev/null 2>&1; B=$(shasum docs/MCP_SIDECAR.md | cut -c1-12); [ "$A" = "$B" ] && echo GENERATOR-IDEMPOTENT || echo GENERATOR-NOT-IDEMPOTENT; echo GUIDE-IMAGES $(ls docs/assets/project-rooms | wc -l); grep -c "Tuesday\|Restart\|walk" docs/PROJECT_ROOMS.md`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cdc8fc90fbc8adb9846fce73b5849fcb9ed4f30f

```text
30 passed in 14.62s
GENERATOR-IDEMPOTENT
GUIDE-IMAGES 14
2
```
