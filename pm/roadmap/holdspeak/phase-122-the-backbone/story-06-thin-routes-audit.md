# HS-122-06 — Thin routes audit

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-01 through HS-122-05
- **Unblocks:** HS-122-07 (MCP server)
- **Owner:** unassigned

## The thesis (the bar)

Stories 01-05 extracted services. This story proves every route handler
is now a thin adapter: deserialize HTTP, identify principal, call
service, serialize response. No route should call `get_database()` or
contain business logic.

When this ships, a grep-based audit confirms:

1. `grep -rn "get_database()" holdspeak/web/routes/` returns zero
   hits (excluding comments and imports).
2. No route handler exceeds ~30 lines.
3. Every route's function body follows the pattern:
   `principal → service.method(principal, ...) → response`.

## Acceptance criteria

- [ ] Zero `get_database()` calls in route handlers.
- [ ] No route handler exceeds 30 lines (excluding type annotations).
- [ ] Every route delegates to a named service method.
- [ ] All existing tests pass.
- [ ] API behavior unchanged (smoke test against the running hub).

## Test plan

- `grep -rn "get_database" holdspeak/web/routes/ | grep -v "#"` → 0
- `uv run pytest -q`
- Manual: hit 5 representative endpoints, verify same responses.
