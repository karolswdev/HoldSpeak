# Evidence - HS-134-03

- **Story:** HS-134-03 - MCP speaks destination
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T22:30:20Z

- **Command:** `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_tools.py tests/unit/test_mcp_phase133*.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a43b66404e84c3bcbb84ce62798ca5427e594912

```text
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 0.97s
```

### Walk harness (dry run) — 2026-08-16

- **Command:** `HOME=$(mktemp -d) uv run python scripts/mcp_walk.py`
- **Exit code:** 0

```text
MCP walk: 24 assertions, 24 passed, 0 failed
```

Key assertions: tool_count_82 PASS, static_resources_14 PASS,
resource_templates_10 PASS, all_schemas_closed PASS.
holdspeak://destinations confirmed in static resource listing.
