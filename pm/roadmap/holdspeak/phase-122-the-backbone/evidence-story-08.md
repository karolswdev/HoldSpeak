# Evidence - HS-122-08

- **Story:** HS-122-08 - MCP resources
- **Status:** done
- **Date:** 2026-08-06

## Proof

### Captured run — 2026-08-07T00:18:44Z

- **Command:** `uv run python -c from holdspeak.mcp.resources import list_resources; r=list_resources(); print(f'{len(r["resources"])} static, {len(r["resourceTemplates"])} templates')`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cb953bb05078736a6b942ad57d9f7c6729af8131

```text
4 static, 3 templates
```
