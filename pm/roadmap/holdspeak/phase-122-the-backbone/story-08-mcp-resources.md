# HS-122-08 — MCP resources

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-07 (MCP server must exist)
- **Unblocks:** HS-122-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

MCP tools are actions. MCP resources are stable, read-oriented context
that an MCP client can pull to understand the desk before acting.

When this ships, the MCP server advertises four resources:

### Static resources

1. **`holdspeak://desk/schema`** — Primitive-kind descriptors:
   kind, product noun, authorability, supported operations,
   sync class.

2. **`holdspeak://desk/verbs`** — Full verb catalog with id, label,
   scope, key, and `server`/`ui_only` designation.

3. **`holdspeak://desk/constitution`** — The agent-facing
   constitutional context (the same content shown in the
   ConstitutionalContextCore).

4. **`holdspeak://desk/inference-targets`** — Available
   profiles/models/targets with readiness status.

### Resource templates

5. **`holdspeak://primitives/{kind}/{id}`** — Canonical detail for
   one primitive.

6. **`holdspeak://workbenches/{id}`** — Workbench detail with items,
   runs, memory.

7. **`holdspeak://meetings/{id}`** — Meeting detail with artifacts.

## Acceptance criteria

- [ ] Four static resources advertised and readable.
- [ ] Three resource templates resolve to real data.
- [ ] Schema resource matches the current `PrimitiveKind` enum.
- [ ] Verbs resource includes the `ui_only` designation.
- [ ] Constitution resource returns the same text as the API.
- [ ] MCP client can read all resources.

## Files in scope

- `holdspeak/mcp/resources.py`
- `holdspeak/mcp/server.py` (resource registration)
