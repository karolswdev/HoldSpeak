# Parked product code

Parked 2026-10-05 (owner, "finish it all up"; owner law: never delete, park).
Each file is kept at its old path under this folder. Nothing here is imported,
packaged (the wheel holds `holdspeak/` only) or tested
(`tests/_parked/conftest.py` stops collection of the one parked test).

A file is parked here only when it has no live user: no importer in
`holdspeak/`, `tests/`, `scripts/`, `uat/`; no string reference (plugin id,
`importlib`, entry point); no HTTP route; no MCP tool; no test besides its own.
The census below is from an `ast` import graph plus `git grep` of the dotted
module name and the file name, on branch `chore/finish-housekeeping`.

| Parked file | Lines | Importers | Why it was dead |
|---|---|---|---|
| `holdspeak/db/models/actions.py` | 162 | none | Stale copy. Every class also lives in `holdspeak/db/models/__init__.py`; 5 of 8 had drifted from it |
| `holdspeak/db/models/activity.py` | 203 | none | Stale copy; 9 of 10 drifted |
| `holdspeak/db/models/infra.py` | 126 | none | Stale copy; 5 of 5 drifted |
| `holdspeak/db/models/knowledge.py` | 236 | one test, now redirected | Stale copy; 9 of 9 drifted. `tests/unit/test_secret_slots.py` tested the sync serializer with this stale `ProfileRecord`; it now uses the real one |
| `holdspeak/db/models/meeting.py` | 103 | none | Stale copy; 5 of 5 drifted |
| `holdspeak/db/models/workbench.py` | 232 | none | Stale copy; 7 of 12 drifted. Its two sites left the routing-authority census (`tests/unit/test_phase143_routing_authority_census.py`) |
| `holdspeak/services/thread_tool_protocol.py` | 85 | none | No importer, no string reference |
| `holdspeak/kernel/voice_resolve.py` | 78 | none | No importer, no string reference (the live voice resolver is `holdspeak/voice_resolver.py`) |
| `holdspeak/web/routes/meetings/_shared.py` | 24 | none | No importer, no string reference |
| `holdspeak/workrooms.py` | 114 | its own test only | HS-93-02 workroom context; no product caller. Its test is parked at `tests/_parked/dead-code/tests/unit/test_workroom_context.py` |

Total: 1,363 lines.

To bring a file back: `git mv parked/<path> <path>` (and its test from
`tests/_parked/dead-code/`).

## Looked at and kept

| File | Why it stays |
|---|---|
| `holdspeak/product_copy.py` | The Phase-93 copy census: `tests/unit/test_product_copy.py` scans live product surfaces for prohibited copy. A live guard, not dead code |
| `holdspeak/connector_fixtures.py` | The fixture dry-run harness that `tests/unit/test_connector_fixture_harness.py` drives against the real connector preview. Test infrastructure in the product package: moving it to `tests/` is a choice for the owner |
| `holdspeak/realtime_frames.py` | The Python canon that `web/src/runtime/frames.ts` mirrors; its test fences the mirror |
| `holdspeak/confluence_templates.py` | `tests/unit/test_hs174_confluence_wire.py` covers it with the live Confluence wire |
| `holdspeak/plugins/builtin/followup_ticket_actuator.py` | Named by plugin id in actuator and mesh tests; a plugin-style load does not show in an import graph |
| `holdspeak/meeting_session/deferred_admission.py` | `queue_service_principal` is used by the Phase 143 meeting-route tests and named in the routing census |
