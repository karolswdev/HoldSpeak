# HS-123-09 — MCP tools: workbench and recipe

- **Project:** holdspeak
- **Phase:** 123
- **Status:** backlog
- **Depends on:** HS-123-01, HS-123-12
- **Unblocks:** HS-123-13
- **Owner:** unassigned

## The thesis (the bar)

MCP must be able to operate the desk's programmable work surfaces without
reimplementing web-route logic or acquiring persistence itself. This story adds
the workbench, recipe, zone, and knowledge-membership verbs as deliberately
small adapters over the service layer.

The implementation belongs in `holdspeak/mcp/tools.py`, using the existing
`TOOLS` catalog, `dispatch(name, arguments, principal)`, `ToolError`, and
`_run()` conventions. Import `RecipeService` alongside the existing
`WorkbenchService` and `PrimitiveService`; construct all three from the one
`get_database()` call already made at the top of `dispatch`. Do not add a new
transport, route call, repository import, or database acquisition below that
construction seam.

## Service contracts to expose

### Workbenches — `holdspeak/services/workbench_service.py`

| MCP tool | Service call |
| --- | --- |
| `workbench.list` | `list_workbenches(principal)` |
| `workbench.get` | `get_workbench(principal, workbench_id)` |
| `workbench.create` | `create_workbench(principal, *, name, **fields)` |
| `workbench.update` | `update_workbench(principal, workbench_id, **fields)` |
| `workbench.delete` | `delete_workbench(principal, workbench_id)` |
| `workbench.update_item` | `update_item(principal, workbench_id, item_id, **fields)` |
| `workbench.delete_item` | `delete_item(principal, workbench_id, item_id)` |
| `workbench.list_runs` | `list_runs(principal, workbench_id)` |

Return deletion results consistently as `{"deleted": true, "id": id}`. Do
not prevalidate service-owned fields: `WorkbenchService` owns required-name,
not-found, active/claimed-item conflict, and item-state rules.

### Recipes — `holdspeak/services/recipe_service.py`

| MCP tool | Service call |
| --- | --- |
| `recipe.list` | `list_recipes(principal)` |
| `recipe.get` | `get_recipe(principal, recipe_id)` |
| `recipe.run` | `await run(principal, recipe_id, input=..., **options)` |
| `recipe.chat` | `await chat(principal, recipe_id, question=..., **options)` |

Both run operations are coroutines. Route them through the existing `_run()`
bridge, extending its error text so it is not falsely specific to workbenches.
Pass only documented option keys rather than forwarding arbitrary MCP fields:
`recipe.run` accepts `variables`, `inference_target_id`, `requested_placement`,
`max_tokens`, `temperature`, `source_ref`, `source_type`, `grounding_refs`,
`grounding_revisions`, `source_revision`, `deadline_at`, and `initiator`;
`recipe.chat` accepts `history`, `grounding`, `inference_target_id`, and
`egress_context`. Never accept or surface a `broadcast` callback over MCP.

### Zone and KB membership — `holdspeak/services/primitive_service.py`

| MCP tool | Service call |
| --- | --- |
| `zone.file` | `file_member(principal, directory_id, primitive_id)` |
| `zone.unfile` | `unfile_member(principal, directory_id, primitive_id)` |
| `zone.list_members` | `list_directory_members(principal, directory_id)` |
| `kb.add_member` | `add_kb_member(principal, kb_id, resource_ref)` |
| `kb.remove_member` | `remove_kb_member(principal, kb_id, resource_ref)` |
| `kb.list_members` | `list_kb_members(principal, kb_id)` |

`zone.unfile` and `kb.remove_member` return the same deletion envelope. Preserve
`PrimitiveService`'s qualified-reference and membership/not-found semantics;
the MCP adapter must not construct relationship records.

## Tool schemas and dispatch shape

Add all eighteen names to `TOOLS`; every schema is an object with
`"additionalProperties": false`. Use `workbench_id`, `recipe_id`,
`directory_id`, `kb_id`, and `item_id` consistently rather than ambiguous `id`.
The following are implementation-grade schema examples; the named `fields` or
`options` object is the forward-compatible service payload boundary.

```json
{
  "name": "workbench.create",
  "description": "Create a Workbench. Use fields for optional Workbench configuration.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Non-empty Workbench name."},
      "fields": {"type": "object", "description": "Optional Workbench fields such as id, recipe_id, profile_id, schedule, or context."}
    },
    "required": ["name"], "additionalProperties": false
  }
}
```

```json
{
  "name": "workbench.update_item",
  "description": "Update supplied fields of a Workbench item.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "workbench_id": {"type": "string"}, "item_id": {"type": "string"},
      "fields": {"type": "object", "description": "Item patch: title, body, priority, status, grounding, context, result, result_egress, tokens_consumed, claimed_at, or completed_at."}
    },
    "required": ["workbench_id", "item_id", "fields"], "additionalProperties": false
  }
}
```

Use the `{id}` read/delete pattern for `workbench.get`, `workbench.delete`, and
`workbench.list_runs`: their required input is `workbench_id`; update additionally
requires `fields`; item deletion requires `workbench_id` and `item_id`.

```json
{
  "name": "recipe.run",
  "description": "Run an Agent recipe and return its lifecycle-backed result and minted artifact reference.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "recipe_id": {"type": "string"}, "input": {"type": "string"},
      "options": {"type": "object", "description": "Optional run fields: variables, inference_target_id, requested_placement, max_tokens, temperature, source_ref, source_type, grounding_refs, grounding_revisions, source_revision, deadline_at, and initiator."}
    },
    "required": ["recipe_id"], "additionalProperties": false
  }
}
```

`recipe.list` has an empty object schema; `recipe.get` requires `recipe_id`.
`recipe.chat` requires `recipe_id` and `question`, with an optional `options`
object limited to `history`, `grounding`, `inference_target_id`, and
`egress_context`.

```json
{
  "name": "zone.file",
  "description": "File a primitive in a Zone.",
  "inputSchema": {
    "type": "object",
    "properties": {"directory_id": {"type": "string"}, "primitive_id": {"type": "string"}},
    "required": ["directory_id", "primitive_id"], "additionalProperties": false
  }
}
```

`zone.unfile` has the same schema and `zone.list_members` requires only
`directory_id`. `kb.add_member` and `kb.remove_member` require `kb_id` plus
`ref` (mapped to the service's `resource_ref`); `kb.list_members` requires only
`kb_id`.

## Tests and verification

Add protocol-level tests beside the current MCP tests (for example,
`tests/test_mcp_tools.py` or the established equivalent). Call
`server.handle_message()` or stdio, not `dispatch()` only, so schemas/catalog,
principal resolution, JSON serialization, and `isError` behavior are covered.
At minimum prove every catalog name; successful workbench creation/update/item
update/run-listing; recipe list/get plus async run/chat with a fake inference
boundary; zone and KB membership lifecycle; and representative not-found,
validation, and claimed/active-item conflict errors. Assert errors are MCP tool
results with `isError: true`, never FastAPI shapes.

```bash
uv run pytest -q tests/ -k 'mcp or workbench or recipe or membership'
uv run pytest -q
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | uv run python -m holdspeak.mcp \
  | python3 -c 'import json,sys; names={t["name"] for t in json.load(sys.stdin)["result"]["tools"]}; required={"workbench.list","workbench.get","workbench.create","workbench.update","workbench.delete","workbench.update_item","workbench.delete_item","workbench.list_runs","recipe.list","recipe.get","recipe.run","recipe.chat","zone.file","zone.unfile","zone.list_members","kb.add_member","kb.remove_member","kb.list_members"}; assert required <= names, sorted(required-names); print(len(names))'
```

## Files in scope

- `holdspeak/mcp/tools.py`
- `holdspeak/mcp/server.py` only if error mapping needs a transport-neutral
  adjustment
- `holdspeak/services/workbench_service.py`
- `holdspeak/services/recipe_service.py`
- `holdspeak/services/primitive_service.py`
- Existing MCP protocol/tool tests and focused service fixtures
