# HS-122-07 — MCP server — 10 tools

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-06 (thin routes — services must exist)
- **Unblocks:** HS-122-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The services exist. Now plug an MCP adapter into them. DeskOS becomes
programmable from any MCP client.

When this ships, a `holdspeak-mcp` Python stdio sidecar serves 10
tools. It follows the DW MCP pattern: static tool registry, JSON
Schema inputs, stdio JSON-RPC loop, no business logic in handlers.

## The 10 day-one tools

| Tool | Service method | What it does |
|------|---------------|-------------|
| `desk.list` | `PrimitiveService.list` | List primitives by kind with query/pagination |
| `desk.get` | `PrimitiveService.get` | Get one primitive's full detail |
| `desk.create` | `PrimitiveService.create` | Create an authorable primitive |
| `desk.update` | `PrimitiveService.update` | Partial update with concurrency |
| `desk.delete` | `PrimitiveService.delete` | Soft-delete with receipt |
| `desk.verb` | Server-side verb dispatcher | Execute allowlisted server verbs; UI-only verbs return `{status: "ui_only"}` |
| `workbench.run` | `WorkbenchService.run` | Trigger a workbench run |
| `workbench.add_item` | `WorkbenchService.add_item` | Add a work item |
| `meeting.list` | `MeetingService.list` | Search/list meetings |
| `meeting.get` | `MeetingService.get` | Get meeting detail with artifacts |

## Architecture

```
Claude Code / MCP client
  └── holdspeak-mcp (Python stdio)
        ├── TOOLS registry (descriptions, JSON Schema)
        ├── JSON-RPC loop (request → dispatch → response)
        └── Service calls (PrimitiveService, WorkbenchService, etc.)
              └── Principal from env token (HOLDSPEAK_TOKEN)
```

## Authentication

- `HOLDSPEAK_URL` environment variable (default `http://127.0.0.1:...`)
- `HOLDSPEAK_TOKEN` environment variable
- The sidecar authenticates as a principal using the existing token
  mechanism.
- The sidecar NEVER prints the token to stdout, logs, or tool results.

## `desk.verb` policy

Server-side verb allowlist only. UI-local verbs (open, snap, cycle,
palette, toggle-view) return:
```json
{"status": "ui_only", "verb_id": "object.open", "reason": "Opens a local surface"}
```

## Acceptance criteria

- [ ] `holdspeak-mcp` executable exists and starts via stdio.
- [ ] 10 tools are advertised via MCP `tools/list`.
- [ ] Each tool calls the corresponding service method.
- [ ] Auth uses environment token, never exposed in output.
- [ ] `desk.verb` rejects UI-only verbs with structured response.
- [ ] Tool errors map to `isError: true` results, not crashes.
- [ ] MCP client (Claude Code) can call all 10 tools successfully.

## Files in scope

- New: `holdspeak/mcp/server.py`
- New: `holdspeak/mcp/tools.py`
- New: `holdspeak/mcp/auth.py`
- `.mcp.json` or equivalent registration
