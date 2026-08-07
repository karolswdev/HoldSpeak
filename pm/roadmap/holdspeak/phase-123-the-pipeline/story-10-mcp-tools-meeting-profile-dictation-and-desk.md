# HS-123-10 — MCP tools: meeting, profile, dictation, and desk

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-01, HS-123-12
- **Unblocks:** HS-123-13
- **Owner:** unassigned

## The thesis (the bar)

The second MCP tool family completes the operational desk: capture can be
controlled, inference destinations managed, journal records inspected, the
whole desk read coherently, and decisions superseded. Each verb must reach the
same service boundary as web clients, carrying an explicit MCP `Principal` and
never reproducing route or persistence logic.

Implement in `holdspeak/mcp/tools.py`: import `DeskService`, `DictationService`,
and `ProfileService`; construct them from the existing single `get_database()`
call in `dispatch`, beside `MeetingService` and `PrimitiveService`. The only
exception is capture control: instantiate `MeetingService` through the same
composition seam used by the meeting route so its `on_start`/`on_stop` callbacks
remain wired. Do not instantiate a bare service that turns a supported capture
controller into `Meeting start control not supported`.

## Service contracts to expose

| MCP tool | Service call | Result requirement |
| --- | --- | --- |
| `meeting.start_capture` | `start_capture(principal, config=None)` | Preserve callback receipt/status payload. |
| `meeting.stop_capture` | `stop_capture(principal, meeting_id=None)` | Preserve existing stop payload; the service currently owns controller selection. |
| `meeting.delete` | `delete_meeting(principal, meeting_id)` | Return `{"deleted": true, "id": meeting_id}`. |
| `meeting.export` | `export_meeting(principal, meeting_id, format)` | Return the canonical export payload and validate `markdown`/`json` in service. |
| `profile.list` | `list_profiles(principal)` | Return profiles and mesh liveness unchanged. |
| `profile.get` | `get_profile(principal, profile_id)` | Service redaction remains authoritative. |
| `profile.create` | `create_profile(principal, fields)` | Pass one fields object; never unwrap/write credentials. |
| `profile.update` | `update_profile(principal, profile_id, patch)` | Pass one patch object. |
| `profile.delete` | `delete_profile(principal, profile_id)` | Return deletion envelope. |
| `dictation.list` | `list_journal(principal, *, limit=200, cursor=None, source=None)` | Forward only accepted paging/filter values. |
| `dictation.get` | `get_entry(principal, entry_id)` | Coerce `entry_id` to integer at the adapter boundary. |
| `desk.snapshot` | `snapshot(principal)` | One coherent initial desk read, not a fan-out of list tools. |
| `decision.supersede` | `PrimitiveService.supersede_decision(principal, decision_id)` | Return successor decision payload. |

`MeetingService.start_capture` accepts `config: dict[str, Any] | None`; the
service currently reads `config["devices"]`. Leave that interpretation there.
`ProfileService` rejects secrets and the built-in `this_machine` target; do not
mirror those checks. `DictationService` accepts source values `dictation`,
`dry_run`, `browser`, and `hotkey`; invalid source filtering remains service
behavior.

## Tool schemas and dispatch shape

Add the thirteen names to `TOOLS` using `inputSchema` objects with
`additionalProperties: false`, clear descriptions that state *when* to invoke
the operation, and field descriptions suitable for an MCP client.

```json
{
  "name": "meeting.start_capture",
  "description": "Start a meeting capture through the configured HoldSpeak capture controller.",
  "inputSchema": {
    "type": "object",
    "properties": {"config": {"type": "object", "description": "Optional capture configuration, including devices."}},
    "additionalProperties": false
  }
}
```

`meeting.stop_capture` takes optional `meeting_id`; `meeting.delete` requires
`meeting_id`; `meeting.export` requires `meeting_id` and `format`, where
`format` is `{"type":"string","enum":["markdown","json"]}`.

```json
{
  "name": "profile.create",
  "description": "Create an inference destination using non-secret profile fields.",
  "inputSchema": {
    "type": "object",
    "properties": {"fields": {"type": "object", "description": "Profile fields; a non-empty name is required by the service."}},
    "required": ["fields"], "additionalProperties": false
  }
}
```

`profile.list` has an empty object schema. `profile.get` and `profile.delete`
require `profile_id`; `profile.update` requires `profile_id` and a `fields`
object mapped to the service's `patch` argument. Never define secret-related
properties in the MCP schema.

```json
{
  "name": "dictation.list",
  "description": "Read the retained dictation journal, optionally paged and filtered by source.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "minimum": 1, "maximum": 500},
      "cursor": {"type": "integer"},
      "source": {"type": "string", "enum": ["dictation", "dry_run", "browser", "hotkey"]}
    },
    "additionalProperties": false
  }
}
```

`dictation.get` requires integer `entry_id`; `desk.snapshot` has an empty
object schema; and `decision.supersede` requires `decision_id`:

```json
{"type":"object","properties":{"decision_id":{"type":"string","description":"Decision to supersede."}},"required":["decision_id"],"additionalProperties":false}
```

## Tests and verification

Extend the existing stdio/protocol test suite to assert every new catalog name,
its required-schema behavior, dispatch principal, JSON result shape, and stable
`isError` failures. Use callback-injected `MeetingService` fixtures to prove
start/stop reaches the controller. Cover export-format validation and
missing-meeting errors; profile creation/update/listing and secret/built-in
refusals; journal pagination/get-not-found; snapshot coherence; and a decision
supersession that produces the successor through `PrimitiveService`.

```bash
uv run pytest -q tests/ -k 'mcp or meeting or profile or dictation or desk'
uv run pytest -q
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | uv run python -m holdspeak.mcp \
  | python3 -c 'import json,sys; names={t["name"] for t in json.load(sys.stdin)["result"]["tools"]}; required={"meeting.start_capture","meeting.stop_capture","meeting.delete","meeting.export","profile.list","profile.get","profile.create","profile.update","profile.delete","dictation.list","dictation.get","desk.snapshot","decision.supersede"}; assert required <= names, sorted(required-names); print(len(names))'
```

## Files in scope

- `holdspeak/mcp/tools.py`
- `holdspeak/mcp/server.py` only for transport-neutral error plumbing
- `holdspeak/services/meeting_service.py`
- `holdspeak/services/profile_service.py`
- `holdspeak/services/dictation_service.py`
- `holdspeak/services/desk_service.py`
- `holdspeak/services/primitive_service.py`
- Existing MCP protocol/tool tests and meeting-controller fixtures
