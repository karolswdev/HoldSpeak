# HS-123-13 — The walk

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** HS-123-09, HS-123-10, HS-123-11, HS-123-12
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The final proof is a real, service-backed desk walk. It starts the hub, drives
the MCP stdio server as a client, proves that each new tool changes or reads
real persisted state, reads every new resource URI, runs the doctor against the
same hub, and renders the resulting desk at desktop and narrow widths.

Add `scripts/desk_walk/walk_mcp_123.py`. It is a deterministic integration
script, not a mock or a direct service-unit test. Reuse the project walk
harness's hub lifecycle, seeded database, cleanup conventions, assertion
helpers, screenshot manifest, and browser connection. If existing helpers live
under `scripts/desk_walk/` or `tests/`, import them rather than reproducing
server startup, JSON-RPC framing, or screenshot plumbing.

## Walk protocol

### MCP client helper

Implement a tiny, explicit stdio client in `scripts/desk_walk/walk_mcp_123.py`
(or use an established one): start `uv run python -m holdspeak.mcp`, send one
newline-delimited JSON-RPC request, read one response, and decode tool text
content as JSON. Use sequential request IDs and assertion helpers that fail
with the method, tool/resource URI, response payload, and relevant IDs. First
invoke `initialize`, `notifications/initialized`, `tools/list`, and
`resources/list`.

Tool call request shape:

```json
{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"workbench.create","arguments":{"name":"MCP 123 Walk","fields":{}}}}
```

Resource read shape:

```json
{"jsonrpc":"2.0","id":13,"method":"resources/read","params":{"uri":"holdspeak://workbenches/<workbench-id>/runs"}}
```

For each successful tool call, assert `result.isError is false`; for intentional
failure legs assert `result.isError is true`, parse the text JSON error, and
assert the stable domain phrase rather than an HTTP status or traceback.

### Required tool matrix

The script must invoke every new Phase 123 tool once, with real IDs produced by
prior calls or the walk seed:

| Family | Required calls and asserted result |
| --- | --- |
| Workbench | `workbench.list`, `get`, `create`, `update`, `update_item`, `delete_item`, `list_runs`, and `delete`; create an item through the pre-existing `workbench.add_item` prerequisite, delete it before deleting its workbench. |
| Recipe | `recipe.list`, `get`, `run`, and `chat`; use a walk recipe/profile whose local inference fixture is deterministic. Assert returned `invocation_id` and/or `artifact_id`, not model prose. |
| Zone / KB | `zone.file`, `zone.list_members`, `zone.unfile`; `kb.add_member`, `kb.list_members`, `kb.remove_member`. Assert membership references before and after removal. |
| Meeting | `meeting.start_capture`, `meeting.stop_capture`, `meeting.export`, and `meeting.delete`; use the hub's real configured capture-controller seam and an archived meeting for export/delete. |
| Profile | `profile.list`, `get`, `create`, `update`, `delete`; assert profile output contains no secret fields. |
| Dictation / desk / decision | `dictation.list`, `dictation.get` with a seeded journal entry, `desk.snapshot`, and `decision.supersede`; assert snapshot includes the created state and supersession returns a distinct successor. |

Include material negative legs: a missing workbench or recipe read, invalid
`meeting.export` format, an invalid/empty profile creation field set, a missing
journal entry, and a duplicate/missing zone or KB membership operation where
its service has a named failure. Do not create irreversible external work or
send network traffic beyond the established local test fixture.

### Required resource matrix

Read every resource added by HS-123-11, and assert the resource list advertised
it before reading:

```text
holdspeak://desk/snapshot
holdspeak://workbenches
holdspeak://workbenches/<workbench-id>/runs
holdspeak://recipes
holdspeak://recipes/<recipe-id>
holdspeak://profiles
holdspeak://profiles/<profile-id>
holdspeak://dictation/journal
holdspeak://zones/<directory-id>/members
```

Validate `contents[0].uri`, `mimeType == "application/json"`, and the expected
canonical payload key/value. For the template resources, use IDs created or
seeded during the same run. This proves URI routing and service ownership rather
than only resource listing.

## Doctor, UI walk, and screenshots

Run the doctor against the same configured hub after MCP state changes:

```bash
uv run python -m holdspeak.doctor
```

Capture complete stdout/stderr and exit status as story evidence; do not claim a
pass from a subprocess return code without reading the recorded output.

Run the normal browser walk twice against the same hub/database state:

```bash
uv run python scripts/desk_walk/walk_mcp_123.py --viewport 1440x900
uv run python scripts/desk_walk/walk_mcp_123.py --viewport 393x852
```

The script must navigate the real desk, wait for its normal readiness signal,
assert that the created/updated workbench, zone/member state, and relevant
object can be opened or observed, then emit screenshot paths through the
existing manifest helper. Store final screenshots beneath:

```text
pm/roadmap/holdspeak/phase-123-the-pipeline/assets/hs-123-13/
```

Use descriptive, stable filenames such as `desk-1440.png` and `desk-393.png`.
The 393px capture must prove that no content is clipped horizontally and that
the relevant state remains reachable, not merely that the page loaded.

## Assertion helpers and tests

All existing walk assertion helpers must pass. Add focused automated coverage
for the new script's protocol helpers, catalog set, error decoder, cleanup, and
viewport manifest; the full live walk remains the integration evidence. Cleanup
must run in `finally` blocks: terminate the stdio child, stop the hub, and
remove only walk-created entities if the project fixture does not reset the DB.

## Acceptance criteria

- [ ] `scripts/desk_walk/walk_mcp_123.py` invokes every HS-123-09 and
      HS-123-10 tool and reads every HS-123-11 resource through stdio MCP.
- [ ] Every success assertion observes real service-backed state; every
      material failure assertion observes stable MCP/domain error behavior.
- [ ] `uv run python -m holdspeak.doctor` passes against the walk hub and its
      complete actual output is captured as evidence.
- [ ] The established walk assertions pass at 1440px and 393px.
- [ ] Desktop and narrow screenshots are present under this story's evidence
      assets and show the resulting desk state.
- [ ] Relevant focused tests and `uv run pytest -q` pass.

## Verification commands

```bash
uv run pytest -q tests/ -k 'mcp or desk_walk or doctor'
uv run python scripts/desk_walk/walk_mcp_123.py --viewport 1440x900
uv run python scripts/desk_walk/walk_mcp_123.py --viewport 393x852
uv run python -m holdspeak.doctor
uv run pytest -q
```

Capture each live command through the Delivery Workbench evidence command when
shipping, read the output, then attach the two screenshots under the story
assets directory before the status can become `done`.

## Files in scope

- `scripts/desk_walk/walk_mcp_123.py` (new)
- Existing helpers and fixtures under `scripts/desk_walk/`, `tests/`, and `web/`
- `holdspeak/mcp/tools.py`, `holdspeak/mcp/resources.py`, and service fixtures
  only when the live walk exposes a defect
- `holdspeak/doctor.py` and related doctor tests only if doctor coverage needs
  an adjustment
- `pm/roadmap/holdspeak/phase-123-the-pipeline/assets/hs-123-13/` when shipping
  the evidence screenshots
