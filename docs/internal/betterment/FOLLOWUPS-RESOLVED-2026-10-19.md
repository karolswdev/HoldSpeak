# Follow-up reconciliation — 2026-10-19

These rows were removed from the open follow-up list after checking the
merged recovery inventory. This records implementation closure, not live
owner acceptance. The original descriptions are retained below.

| Item | Merged repair |
|---|---|
| Q0 model context | E3 #1294, already marked fixed in the old list |
| A3 result cost | M2 #1301, already marked fixed in the old list |
| A8 old New Agent/New Zone docs | #1345 menu docs and #1368 current desk documentation |
| Q6 phone About chips | #1341 |
| D5 eleven retired Brief atlas cases | #1353 |
| A6 lane source-file race | #1343 |

Original rows:

| Found in | Follow-up | Goes to |
|---|---|---|
| ~~Q0 (#1260)~~ FIXED in E3 #1294 | An engine added through the Model Library gets a 16,384-token context by default (`model_library_service.py:526`), although the LAN engine serves 49,152. The route also counts one token per byte (`inference_adoption_service.py:148-157`). Tools barely fit. Read the engine's real context size when Check runs, and count tokens properly. | Engines E3 |
| ~~A3 (#1293)~~ FIXED in M2 #1301 | Results carry no cost yet (E2 stores CLI cost per engine run, not on the result). | Automations A6 / MCP M2 |
| A8 (#1325) | `docs/WEB_DESK.md` and `docs/DESK_OBJECT_MODEL.md` still list New Agent and New Zone (parked earlier). | Small fix |
| A6 lane | `tests/unit/test_project_mcp.py:370` writes and deletes a file inside `holdspeak/` while `test_thread_tool_gate.py` walks it in parallel: FileNotFoundError race. | Small fix |
| Q6 (#1335) | At 393 the About chips sit in stray boxed frames with an odd indent. | Small fix |
| D5 (#1336) | Eleven atlas cases (no fence runs them) still click the retired Brief window, incl. `route_generate_again.retained_after_reload`, named as a successor (#1338). | Small fix |


P5/P6 source-link follow-through: the producer reports each meeting/note as
linked or failed for new and existing projects. Failed selections retain the
producer error and Retry submits only that leaf. Root verified 57 Python checks
(including actual HTTP and 1440/393 browser Retry), 40 Door web checks and build.
Durable readback finds each successful relationship once. No slice count added.
