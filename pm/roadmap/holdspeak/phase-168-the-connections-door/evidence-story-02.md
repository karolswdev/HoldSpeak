# Evidence - HS-168-02

- **Story:** HS-168-02 - The connections service (one readiness shape; the suggest step annotated; known scopes; MCP twins)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-04T04:11:03Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_hs168_connections_service.py tests/web/test_hs168_connections_routes.py tests/mcp/test_hs168_connection_tools.py tests/unit/test_project_setup_service.py tests/unit/test_project_mcp_palette.py tests/unit/test_thread_tool_gate.py tests/unit/test_mcp_sidecar_doc_drift.py tests/integration/test_project_setup_routes.py tests/unit/test_github_provider.py tests/unit/test_jira_provider.py 2>&1 | tail -3 && uv run python scripts/gen_mcp_sidecar_doc.py --check 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d48faaf52182afbcb1d16a2c29592f17a5034a49

```text
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
357 passed, 2 skipped in 75.88s (0:01:15)
  189 tools across 34 families
```
