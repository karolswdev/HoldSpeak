# HS-123-12 — Thin routes audit (final)

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-02, HS-123-03, HS-123-04, HS-123-05, HS-123-06, HS-123-07, HS-123-08
- **Unblocks:** HS-123-09, HS-123-10, HS-123-11, HS-123-13
- **Owner:** unassigned

## The thesis (the bar)

This is the mechanical proof that Phase 123 moved ownership out of HTTP
handlers. A thin route is transport adaptation only: deserialize, acquire a
principal, construct/use a named service, and serialize the result. It must not
acquire the database outside its local service constructor, directly use a
repository, own business validation, or orchestrate cross-domain state.

The audit covers every Python route under `holdspeak/web/routes/`, including
nested primitive routes. It also establishes the final MCP catalog threshold
needed by the phase: the baseline 10 tools plus HS-123-09's 18 and
HS-123-10's 13 means `tools/list` must advertise at least 41 tools (the required
floor remains `>= 36` to allow independently valid catalog composition).

## Audit method

### 1. Database-acquisition census

Run this exact command and save its output in story evidence when shipping:

```bash
grep -rn "get_database()" holdspeak/web/routes/ --include="*.py" \
  | grep -v "_svc\|_service\|def _svc\|return.*Service(get_database\|_shared.py\|#"
```

Expected result: no lines. Each remaining line is a handler-level persistence
acquisition until proven otherwise. Move its operation into a named service,
make the route call that service, and add/adjust the service test. Do not add a
new grep exemption merely to pass the census; a true construction exception
must be documented in the route near the constructor and in the audit test.

### 2. Handler body limit

Every endpoint handler must be 30 physical lines or fewer from its `def`/
`async def` declaration through its final executable/return line. Blank lines,
decorators, and comments are excluded; nested helper logic counts. Extract
anything beyond transport adaptation into `holdspeak/services/<domain>_service.py`
or the existing owning service. Keep the route's response model and exception
translation at the transport edge.

Create or update a structural test that parses route modules with `ast`, walks
`FunctionDef` and `AsyncFunctionDef` endpoint functions, and fails with
`path:function:line_count` for a handler over 30 executable-span lines. Exclude
only private `_svc`/`_service` constructors and test-only helpers by a named,
small predicate. Do not perform a fragile text scan that mistakes multiline
signatures for handler bodies.

### 3. Route ownership inventory

For every route touched by HS-123-02 through HS-123-08, record the concrete
service owner in the structural-audit fixture or parameterized test. Examples
include `SettingsService`, `AskService`, `ProjectService`, `MeetingService`,
`ActivityService`, `ProfileService`, `DictationService`, `DeskService`, and
`PrimitiveService`. The test should assert source-level facts that prevent a
regression: no repository imports from a handler module; no direct
`get_database()` except local service constructors; and a named service call in
each route operation.

### 4. MCP catalog audit

After HS-123-09 and HS-123-10 are present, call the stdio server and assert the
full essential subset, not only a count. The required names are the 18 workbench/
recipe/membership tools in Story 09 and the 13 meeting/profile/dictation/desk
tools in Story 10. Tool definitions remain the `TOOLS` objects in
`holdspeak/mcp/tools.py`: each requires `name`, `description`, and an
`inputSchema` object with `additionalProperties: false`.

Example catalog assertion input:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list"}
```

## Acceptance criteria

- [ ] The database census command returns no handler-level lines.
- [ ] The AST-backed handler audit reports no endpoint body over 30 lines.
- [ ] Routes perform only transport adaptation; all business work has a named
      service owner and service-level test coverage.
- [ ] No route module imports or calls a repository directly.
- [ ] `tools/list` contains every required Phase 123 MCP tool and at least 36
      tools overall.
- [ ] Focused structural tests and the full test suite pass.

## Verification commands

```bash
# Must print no matches (grep exit 1 is the successful census condition).
grep -rn "get_database()" holdspeak/web/routes/ --include="*.py" \
  | grep -v "_svc\|_service\|def _svc\|return.*Service(get_database\|_shared.py\|#"

# The new structural test; replace the path only with the actual established test path.
uv run pytest -q tests/ -k 'thin_route or route_audit or mcp'

# Catalog count and named-surface proof.
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | uv run python -m holdspeak.mcp \
  | python3 -c 'import json,sys; tools=json.load(sys.stdin)["result"]["tools"]; names={t["name"] for t in tools}; assert len(tools)>=36, len(tools); required={"workbench.list","workbench.get","workbench.create","workbench.update","workbench.delete","workbench.update_item","workbench.delete_item","workbench.list_runs","recipe.list","recipe.get","recipe.run","recipe.chat","zone.file","zone.unfile","zone.list_members","kb.add_member","kb.remove_member","kb.list_members","meeting.start_capture","meeting.stop_capture","meeting.delete","meeting.export","profile.list","profile.get","profile.create","profile.update","profile.delete","dictation.list","dictation.get","desk.snapshot","decision.supersede"}; assert required <= names, sorted(required-names); assert all(t.get("description") and t.get("inputSchema",{}).get("additionalProperties") is False for t in tools); print(len(tools))'

uv run pytest -q
```

For the first command, run it once under `set +e` or capture its output before
asserting its expected exit status; an empty result normally gives the final
`grep` exit code 1 and is not an audit failure.

## Files in scope

- `holdspeak/web/routes/**/*.py`
- `holdspeak/services/**/*.py`
- `holdspeak/mcp/tools.py`
- Structural audit tests and route/service inventory fixtures under `tests/`
