# HS-123-11 — MCP resources expansion

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01, HS-123-12
- **Unblocks:** HS-123-13
- **Owner:** unassigned

## The thesis (the bar)

Tools perform named operations; resources provide stable, directly readable
context for an MCP client deciding what to do. This story makes the desk
snapshot, workbenches and runs, recipes, profiles, dictation journal, and zone
membership discoverable through canonical service reads.

Implement in `holdspeak/mcp/resources.py`, following its existing
`_STATIC_RESOURCES`, `_RESOURCE_TEMPLATES`, regex matcher, `_contents()`, and
`read_resource(uri, principal)` pattern. Import `DeskService`, `RecipeService`,
and `DictationService`; construct services only at resource dispatch through
`get_database()`, as the existing adapter does. Resource reads take the
principal supplied by `resolve_auth()` in `holdspeak/mcp/server.py`; no route,
repository, or HTTP response object may enter this path.

## Resource contract

All data resources use `mimeType: "application/json"` and serialize through
`_contents(uri, _JSON_MIME, value)`, retaining sorted JSON and the current MCP
`contents` envelope. Add the concrete resources and templates below.

| URI / template | Descriptor location | Service method |
| --- | --- | --- |
| `holdspeak://desk/snapshot` | `_STATIC_RESOURCES` | `DeskService(db).snapshot(principal)` |
| `holdspeak://workbenches` | `_STATIC_RESOURCES` | `WorkbenchService(db).list_workbenches(principal)` |
| `holdspeak://workbenches/{id}/runs` | `_RESOURCE_TEMPLATES` | `WorkbenchService(db).list_runs(principal, id)` |
| `holdspeak://recipes` | `_STATIC_RESOURCES` | `RecipeService(db).list_recipes(principal)` |
| `holdspeak://recipes/{id}` | `_RESOURCE_TEMPLATES` | `RecipeService(db).get_recipe(principal, id)` |
| `holdspeak://profiles` | `_STATIC_RESOURCES` | `ProfileService(db).list_profiles(principal)` |
| `holdspeak://profiles/{id}` | `_RESOURCE_TEMPLATES` | `ProfileService(db).get_profile(principal, id)` |
| `holdspeak://dictation/journal` | `_STATIC_RESOURCES` | `DictationService(db).list_journal(principal)` |
| `holdspeak://zones/{id}/members` | `_RESOURCE_TEMPLATES` | `PrimitiveService(db).list_directory_members(principal, id)` |

Keep the existing `holdspeak://workbenches/{id}` detail resource. Add anchored
patterns for each new template, for example:

```python
_WORKBENCH_RUNS_PATTERN = re.compile(r"^holdspeak://workbenches/([^/]+)/runs$")
_RECIPE_DETAIL_PATTERN = re.compile(r"^holdspeak://recipes/([^/]+)$")
_PROFILE_DETAIL_PATTERN = re.compile(r"^holdspeak://profiles/([^/]+)$")
_ZONE_MEMBERS_PATTERN = re.compile(r"^holdspeak://zones/([^/]+)/members$")
```

Match exact URI order carefully: static URIs first, then parameterized patterns.
Resource templates must use the same `{id}` placeholder shown in listing, and
each descriptor needs a precise name and description explaining its canonical
payload rather than merely restating the URI.

## Resource input examples

Resources do not have tool JSON Schemas; their typed input is the MCP
`resources/read` URI parameter. The required wire forms are:

```json
{"jsonrpc":"2.0","id":7,"method":"resources/read","params":{"uri":"holdspeak://desk/snapshot"}}
```

```json
{"jsonrpc":"2.0","id":8,"method":"resources/read","params":{"uri":"holdspeak://workbenches/wb-123/runs"}}
```

```json
{"jsonrpc":"2.0","id":9,"method":"resources/read","params":{"uri":"holdspeak://zones/dir-123/members"}}
```

No query-string paging is introduced in this story: resources deliberately map
to the service defaults. Use tools where callers need an operation with an input
schema or optional filters.

## Error and redaction behavior

Do not catch and reshape service domain errors inside `resources.py`; let them
reach the existing `ResourceError`/`ValueError` handling in `server.py`, which
maps resource failures to JSON-RPC `-32002`. Unknown URI remains `ResourceError
("Unknown resource: …")`. Missing recipe/profile/workbench/zone data must
retain the named `NotFound` message emitted by its service. Profile reads must
use `ProfileService`, not raw profile records, so its response remains the
redacted canonical contract.

## Tests and verification

Add resource-list and resource-read tests through `handle_message()` or actual
stdio. Assert the nine descriptors/templates are advertised, every URI returns
`contents[0]` with its requested URI and `application/json`, parsed payloads
come from service fixtures, and every parameterized pattern accepts only its
exact form. Include unknown URI, missing recipe/profile/zone, and malformed
resource-read request paths. Spy or fixture service construction as necessary
to prove no route is called.

```bash
uv run pytest -q tests/ -k 'mcp and resource'
uv run pytest -q
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"resources/list"}' \
  | uv run python -m holdspeak.mcp \
  | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; uris={x["uri"] for x in r["resources"]}; templates={x["uriTemplate"] for x in r["resourceTemplates"]}; assert {"holdspeak://desk/snapshot","holdspeak://workbenches","holdspeak://recipes","holdspeak://profiles","holdspeak://dictation/journal"} <= uris; assert {"holdspeak://workbenches/{id}/runs","holdspeak://recipes/{id}","holdspeak://profiles/{id}","holdspeak://zones/{id}/members"} <= templates; print(len(uris), len(templates))'
```

## Files in scope

- `holdspeak/mcp/resources.py`
- `holdspeak/mcp/server.py` only if resource error translation needs a
  transport-neutral correction
- `holdspeak/services/desk_service.py`
- `holdspeak/services/workbench_service.py`
- `holdspeak/services/recipe_service.py`
- `holdspeak/services/profile_service.py`
- `holdspeak/services/dictation_service.py`
- `holdspeak/services/primitive_service.py`
- Existing MCP resource/protocol tests
