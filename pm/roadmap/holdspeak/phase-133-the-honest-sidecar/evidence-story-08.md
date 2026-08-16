# Evidence - HS-133-08

- **Story:** HS-133-08 - The honest handshake
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T16:36:15Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ykHRzxg6aL uv run pytest -q tests/unit/test_mcp_phase133_auth.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e7cc8a95ef3a34461f8adc1307d37b827aae5f49

```text
...                                                                      [100%]
3 passed in 0.08s
```

### Captured run — 2026-08-16T16:36:21Z

- **Command:** `sh -c echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"0.1\"}}}" | HOME=$(mktemp -d) uv run holdspeak-mcp`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e7cc8a95ef3a34461f8adc1307d37b827aae5f49

```text
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": false}, "resources": {"listChanged": false, "subscribe": false}}, "serverInfo": {"name": "holdspeak-mcp", "version": "0.4.0"}}}
```
