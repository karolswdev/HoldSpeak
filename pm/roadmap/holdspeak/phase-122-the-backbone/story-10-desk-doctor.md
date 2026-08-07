# HS-122-10 — Desk doctor

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-07 (MCP server)
- **Unblocks:** HS-122-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The Delivery Workbench has `dw doctor`. The desk needs `desk doctor` —
a deterministic CLI health check that verifies the runtime is ready
and the UI bootstraps correctly.

When this ships, `holdspeak doctor` (or `python -m holdspeak.doctor`)
runs these checks and reports PASS/FAIL/SKIP:

1. **Hub health** — `GET /health` returns `{"status":"ok"}`.
2. **Runtime status** — `/api/runtime/status` returns ready.
3. **WebSocket** — Connect, receive a frame, disconnect.
4. **Desk bootstrap** — `GET /_built/` returns 200 with HTML.
5. **Auth** — Token resolves to a valid principal.
6. **MCP** — `holdspeak-mcp` starts and responds to `tools/list`.
7. **Inference** — At least one inference target is available.
8. **Database** — Service layer can list primitives without error.

Output format:
```
PASS  hub-health        /health → ok
PASS  runtime-status    ready
PASS  websocket         frame received in 340ms
PASS  desk-bootstrap    /_built/ → 200
PASS  auth              principal: owner
PASS  mcp-server        10 tools advertised
SKIP  inference         no targets configured
PASS  database          primitives readable

7 PASS · 1 SKIP · 0 FAIL
```

## Acceptance criteria

- [ ] `holdspeak doctor` runs all 8 checks.
- [ ] Output is machine-parseable (one line per check, status + name).
- [ ] Exit code 0 if all pass/skip, 1 if any fail.
- [ ] Runs without browser or GUI.
- [ ] Works against a local or remote hub (configurable URL/token).

## Files in scope

- New: `holdspeak/doctor.py`
- New: `holdspeak/__main__.py` or CLI entry point
