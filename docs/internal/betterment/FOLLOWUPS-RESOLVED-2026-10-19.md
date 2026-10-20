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

Project update read state: the completed automation artifact stores its exact project-update ID. Room NEW follows that artifact, and opening the linked update uses the existing result-open receipt to mark it read. Legacy and foreign IDs open the automation instead of selecting an owner draft. Root verified five real runner/producer cases and both browser widths, 44 web consumers, type check and build. The recorded consumer uses complete real completed/opened/read responses.


## Audit — 2026-10-20

These implementation entries were already merged. Current source and retained
checks support their closure; live owner acceptance is separate.

| Found in | Delivered by | Current source and proof |
|---|---|---|
| D3 (#1296) · list_action_items(include_completed=False) | #1319 | `holdspeak/db/meetings.py:1202`; `tests/unit/test_cadence_kept_actions.py:54`. Pending and open actions remain live; collector creates one kept-action loop and excludes a duplicate decision commitment. |
| M2 (#1301) · After each item the runner makes a second engine call | #1319 | `holdspeak/services/workbench_runner.py:576`; `tests/integration/test_desk_automations_mcp.py:116`. Memory adapter uses desk_tools=False; actual integration asserts no MCP config or credential for memory and strict MCP isolation. |
| A3 (#1293) · What it has learned | #1304 | `web/src/desk/components/automation/AutomationWindow.tsx:182`; `web/src/desk/__tests__/automation.app.test.tsx:319`. Fold uses lessonWords; consumer asserts 2 lessons. Zero hides the fold. Independently included in root S8 green run of all 4079 web tests. |
| D4 (#1303) · menu bar still has an "Intelligence" menu | #1303 | `web/src/desk/components/DeskMenuBar.tsx:73`; `web/src/desk/__tests__/menus.app.test.tsx:231`. Today object menu title is Today. Consumer verifies the actual target and menu title. Independently included in root S8 green run of all 4079 web tests. |
| Q0 (#1260) · Engine not reachable | #1267 | `holdspeak/services/ask_service.py:961`; `tests/unit/test_desk_room_ask.py`. An assigned route skipped as binding_not_ready without physical dispatch maps to not_reachable, separate from no_assignment/no_engine. Retained actual receipt route classification. |

Original rows:

| Found in | Follow-up | Goes to |
|---|---|---|
| D3 (#1296) | `list_action_items(include_completed=False)` reads only `pending`, but Confirm (and now keep-on-arrival) writes `open`; the cadence collector (`holdspeak/cadence/collector.py:94`) probably never makes loops for confirmed items. | Small fix |
| M2 (#1301) | After each item the runner makes a second engine call ("what should future runs remember?"). On a CLI engine it also gets the desk tools and its own bill. RULING (orchestrator): the memory call runs WITHOUT tools; small fix. | Small fix |
| A3 (#1293) | "What it has learned" shows a bare count ("2"); use words ("2 lessons") or nothing. | Automations A4 |
| D4 (#1303) | The menu bar still has an "Intelligence" menu when Today is front; it should say Today (PLAN §2: Intelligence is retired as a name). | Daily D5 |
| Q0 (#1260) | "Engine not reachable" is shown as "No engine for answers" (`ask_service.py` reason mapping). | Asking Q1 |

Search and Floor follow-through: protected People references use the shared
Object verbs and canonical Desk directory. Keep and Remove persist through
the admitted filing path. Mode recipes retain their semantic kind in Search;
automation aliases resolve the app. Builder tools is a hub setting with saved
revision, agent-readable state and cross-browser refresh. Root verified all
four real browser cases, 65 focused backend/browser cases, 150 web consumers,
and complete Settings producer recordings.

The old Interview ordering entry was already fixed in #1302:
`holdspeak/services/thread_service.py:198` keeps the observation system message
before the user; `tests/unit/test_desk_ask.py:199` retains the exact role-order
assertion and strips tool-call markup. This is implementation closure.

Original rows:

| S4 delivery | The floor and meeting Keep behavior are verified. Mode recipes still enter Search as Agent rows; individual People need their Object-menu adapter because the world stores only the People singleton. Finish both seams in S5. S4 remains partial. | Shell S5 |
| Q0 (#1260) | Interview's answer-only pass puts a system message after the user message, which Qwen's template rejects. | Asking Q4, or a small fix |
| S1 (#1259) | A person is not a desk object, so a person has no Object menu. | Shell S4 or Daily D6 |
| S1 (#1259) | The Builder tools switch is saved in the browser, not on the hub, so an agent cannot read or set it. | Shell S5 |
| S0 (#1257) | Search for "automation" still finds nothing. | Shell S5 (Automations A1 adds the alias) |

Runtime route parity: speech refuses the global chat fallback, and installed
meeting plugins follow the saved summary assignment. The face and frozen
route now share the existing assignment policy. Private SQLite regressions
prove source/profile identity; no live provider or owner assignment was changed.

ST0 remaining Setup facts: Other devices uses durable Config.remote through
SettingsService, and all remote projections read that store. The real private
Hub restart preserves the switch, host and partial port edit. Active Guide
rows name Works / Not ready / Does not work, retaining their reasons and
only existing fix verbs. Seventy-seven backend and six recorded consumer
checks pass; parked Setup faces are unchanged.
