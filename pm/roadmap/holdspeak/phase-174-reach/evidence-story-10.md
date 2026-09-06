# Evidence - HS-174-10

- **Story:** HS-174-10 - The docs (MCP_SIDECAR.md extended, the guide's companions section, remote in the architecture)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T21:03:16Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_doc_drift_guard.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_hs169_room_copy.py 2>&1 | grep -E "[0-9]+ (passed|failed)" | tail -1; echo "markers: $(grep -rn "verify at build" README.md docs/ | wc -l | tr -d " ")"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 36d5e7c260cebda6185eb067f331f2a3865705c1

```text
35 passed in 2.34s
markers: 0
```
