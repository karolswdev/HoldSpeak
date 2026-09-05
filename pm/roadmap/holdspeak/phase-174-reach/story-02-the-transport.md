# HS-174-02 — The transport

- **Project:** holdspeak
- **Phase:** 174
- **Status:** backlog
- **Depends on:** HS-174-01
- **Unblocks:** HS-174-03, HS-174-04, HS-174-05, HS-174-08
- **Owner:** unassigned

## Problem

The MCP sidecar speaks stdio only (holdspeak/mcp/server.py:116-151,
protocol `2024-11-05`). A remote machine (the .43 box, a teammate's
laptop on the tailnet) cannot drive the desk. MCP-008's charter requires
a Streamable HTTP transport on the hub so that remote MCP clients reach
the same services the web UI and the sidecar use — one implementation,
three transports.

## Scope

- In:
  - A Streamable HTTP route on the hub (FastAPI), behind the existing
    `_web_auth_gate` (web_server.py:367-386), calling
    `handle_message()` (server.py:30-107).
  - The remote handler composes on the web runtime's live services (the
    conductor's `set_scheduler_services` seam, the wired fetcher) —
    never the sidecar's bare instances (this pays the 165 fetcher-seam
    debt: holdspeak/mcp/server.py starts its own service layer, while
    the web runtime has the live one).
  - The MCP protocol version bumped honestly (from `2024-11-05` to the
    Streamable HTTP revision); the census of protocol changes
    documented.
  - Parity tests: every tool that passes over stdio must pass over
    HTTP with the same results (MCP-001).
- Out:
  - Identity / credential scoping (story 03).
  - Egress badges (story 04).
  - SSE push (story 05, and only if the spec is ratified).
  - A hosted relay or proxy (Article III:1).

## Acceptance criteria

- [ ] `POST /api/mcp` (or the Streamable HTTP route path) accepts a
      JSON-RPC request and returns a JSON-RPC response; the protocol
      version is the Streamable HTTP revision.
- [ ] The remote handler composes on the web runtime's services (the
      fetcher-seam debt paid; the sidecar's bare instances are not used
      by the remote path).
- [ ] Every tool that passes over stdio passes over HTTP with
      identical results (parity tests; MCP-001).
- [ ] A non-loopback request without a valid credential is refused
      (web_auth.py:73-89).
- [ ] The protocol version bump is documented in MCP_SIDECAR.md.

## Test plan

- Unit: test the Streamable HTTP route with mocked services (dict in,
  dict out shape preserved).
- Integration: parity test matrix — a fixed set of tool calls run over
  stdio and HTTP, results diffed.
- Manual: a real HTTP client (curl or a Python script) from the same
  machine calls the route; the response matches the sidecar's.

## Notes / open questions

- The route path: `/api/mcp` is the natural home. Confirm there is no
  collision with existing routes.
- The Streamable HTTP spec revision (`2025-03-26`) may have moved since
  the handover's recon. Verify the current revision at charter time.
