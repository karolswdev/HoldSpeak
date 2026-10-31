# Betterment tracker

One row for each recipe slice, with the PR that delivered it. Update this
file in the same PR as `pm/STATUS.md`, after each batch. "Done" means
merged to main. "On his desk" is the backend commit in `pm/STATUS.md`.
Open work that is not a slice is in `FOLLOWUPS.md`.

**Last updated:** 2026-10-23, shared surface modernization; owner visual acceptance remains open. Running-desk identity is in `pm/STATUS.md`.


React desktop design proposal (2026-10-23): [merged #1435](https://github.com/karolswdev/HoldSpeak/pull/1435)
connects the [47 workflow reviews](native-experience/adversarial/README.md)
to a [product design](native-experience/DESIGN-PROPOSAL.md),
[seven whole jobs](native-experience/design-proposal/JOURNEYS.md),
[nine paired canvas studies](native-experience/design-proposal/CANVASES.md)
and a [derived delivery plan](native-experience/DELIVERY-PLAN.md).
The owner has now authorized Astra / Sol High execution. The first partial repository/window/reference slice merged in #1438. The
Settings You/shared Forms slice is #1439, built and verified; active
Thought/input follows. [Execution](native-experience/EXECUTION.md) tracks all
ten packages; no recipe count or owner-acceptance state is promoted by a
partial framework slice.

Shared surface framework and reference (2026-10-23): #1428
implements the owner's across-the-board scope: working in-desk patterns,
shared interior adoption, canonical front-window authority and current author
documentation. Existing recipe slices only; no count change. Scope and actual
coverage: `MODERNIZATION-IMPLEMENTATION-2026-10-22.md`. Owner visual judgment
remains open.

Pressed-state fix-forward (2026-10-22): #1425 preserves primary/danger
selection fills during hover and keyboard focus after #1424. Existing slices
only; no count change.

Richer icon correction (2026-10-22): #1427 redraws the family after the
owner rejected #1426 as too basic and toilet-shaped. Angled desktop objects,
visible materials and distinct portraits replace the repeated basin geometry.
The first illustrated SVGs and PNGs are parked; owner aesthetic acceptance
remains open. Scope: RICHER-ICONS-2026-10-22.md.

Shared illustrated icon follow-up (2026-10-22): #1426 replaces the
pixel-art family with crisp illustrated shared app/object/Settings icons.
Existing recipe slices only; owner aesthetic acceptance remains open.

**Total: 115 of 151 slices merged** (Programs added 2026-10-28: 18 slices, 11 in the Programs PR, not merged yet; Phone added 2026-10-28: 16 slices, 10 in the Phone PR, not merged yet; the app's 8 steps are the Program `program-29a6d2ef5d55` and are not counted).
Merged means implementation on main; delivery and owner acceptance are tracked separately in `pm/STATUS.md`.
Codex took delivery on 2026-10-19 at the owner's request. See `RECOVERY-2026-10-19.md` for the interrupted worktrees and PRs.

| Cluster | Folder | Done |
|---|---|---|
| Automations | `workbench/` | 11 of 11 |
| Engines | `engines/` | 8 of 8 |
| The desk's tools (MCP) | `mcp/` | 7 of 7 |
| Ask | `asking/` | 13 of 13 |
| Projects | `projects/` | 11 of 11 |
| Agents | `agents/` | 16 of 16 |
| Daily and Needs you | `daily/` | 11 of 11 |
| Setup and Settings | `setup/` | 10 of 10 |
| Desk shell | `shell/` | 9 of 10 |
| Send | `send/` | 7 of 8 |
| Capture | `capture/` | 12 of 12 |
| Programs | `programs/` | 0 of 18 (PG1–PG11 in the Programs PR) |
| Phone | `phone/` | 0 of 16 (PH1–PH10 in the Phone PR) |

Owner feedback follow-up (2026-10-21): #1419 implements a guided Automation
builder and one-category Settings with pictograms and clearer dropdowns. This
improves the existing A3/A4/A5/A6 and Settings slices; it adds no recipe count.
Original reports: `46bda55a89ce3feb83e0e79e77b71e9a` and
`b3a536d4972f39390bd9e5ce7fb88937`. The owner's live design judgment remains open.

Owner Ask feedback follow-up (2026-10-21): #1421 repairs Enter clearing
and preserves follow-up drafts while replacing the giant empty editor with a
compact composer and paper conversation. Existing Q slices only, no new count.
Original report: `3c7c52ae3ccfdd5ee7e29ddaadaf10e6`. Owner live design judgment remains open.

Shared design follow-up (2026-10-21): #1422 develops the conversation
material and ComposerWell in the library, with live Ask/saved-thread adoption and the retained parked PR
reply composer. /companion opens Agents; PR reply adoption is not live. This improves existing slices without changing their count;
owner aesthetic acceptance remains open.

Shared design fix-forward (2026-10-21): #1423 preserves reading-end
anchoring as Tools opens, makes editor material ownership explicit, and adds
a working local composer specimen to /design/components. The retained PR
reply consumer is parked; no live PR send or aesthetic acceptance is claimed.

Shared shell modernization (2026-10-22): #1424 implements the owner's
“Workbench meets PopOS” direction in common shell/control material, with Ask
and Settings as representative faces. It adds no recipe count and does not
claim aesthetic acceptance or closure of the remaining full-tape failures.

## Automations (`workbench/RECIPE.md`): 11 of 11

| Slice | What | State | Note |
|---|---|---|---|
| A0 | Tell the truth (backend repairs, no new face) | Done · #1256 |  |
| A1 | The name, and finding it | Done · #1270 |  |
| A2 | One automation = one instruction + sources; each run = one result | Done · #1280 |  |
| A3 | The automation window | Done · #1293 |  |
| A4 | When, and With | Done · #1304 |  |
| A5 | About | Done · #1309 |  |
| A6 | Put it in, and where results show up | Done · #1322 |  |
| A7 | Home, New automation, and starters | Done · #1314 |  |
| A8 | Park what the sentence replaces | Done · #1325 |  |
| A9 | Old automations | Done · #1318 |  |
| A10 | An agent works in a folder (after Engines E1) | Done · #1324 |  |

## Engines (`engines/RECIPE.md`): 8 of 8

| Slice | What | State | Note |
|---|---|---|---|
| E0 | Shots of today | Done · #1249 |  |
| E1 | The agent CLI engine (backend) | Done · #1273 |  |
| E2 | Found on this Mac, and one-press Add | Done · #1279 |  |
| E3 | The model picker, and one engine for each model | Done · #1294 |  |
| E4 | Add an engine, by kind | Done · #1311 |  |
| E5 | What runs where | Done · #1315 |  |
| E6 | One name | Done · #1320 |  |
| E7 | pi and Gemini CLI presets | Done · #1323 |  |

## The desk's tools (MCP) (`mcp/RECIPE.md`): 7 of 7

| Slice | What | State | Note |
|---|---|---|---|
| M0 | Settle the unknowns (a live check, not a PR) | Done · #1266 |  |
| M1 | One-shot runs with the desk's tools | Done · #1278 |  |
| M2 | Looked at, Wrote, Prepared | Done · #1301 |  |
| M3 | Automations on MCP | Done · #1319 |  |
| M4 | Engines on MCP | Done · #1321 |  |
| M5 | Tools for HTTP engines that accept tool calls | Done · #1330 |  |
| M6 | A GitHub pull-request read | Done · #1331 |  |

## Ask (`asking/RECIPE.md`): 13 of 13

| Slice | What | State | Note |
|---|---|---|---|
| Q0 | Threads tell the truth | Done · #1260 |  |
| Q1 | The Room's Ask tells the truth | Done · #1267 |  |
| Q2 | Ask goes first | Done · #1269 |  |
| Q3 | Search asks | Done · #1332 |  |
| Q4 | One Ask window | Done · #1302 |  |
| Q5 | Ask about this, from everywhere | Done · #1335 |  |
| Q6 | The About picker | Done · #1335 | Shared picker A5 #1309; shortcuts/chips/drop #1335; phone chip layout fixed #1341. |
| Q7 | Ask my whole desk | Done · #1305 |  |
| Q8 | One note | Done · #1351 | Phone footer follow-up delivered with #1368. |
| Q9 | Find the tasks | Done · #1354 | Privacy fix #1362 merged; operations/MCP/Edit/Dismiss follow-up #1365 merged. |
| Q10 | Knowledge becomes drawers | Done · #1368 | Existing collections, About chips and filing use named drawers; data and tools retained. |
| Q11 | Memory where he looks | Done · #1375 | Pages have their own pass budget and engine fallback; distinct person answers retain working sources. |
| Q12 | The Memory app | Done · #1375 | Go opens desk answers, Why and links; whole-desk Ask and RAW Recall retained. |

## Projects (`projects/RECIPE.md`): 11 of 11

| Slice | What | State | Note |
|---|---|---|---|
| P0 | Draft update never freezes the desk and never goes quiet | Done · #1253 |  |
| P1 | Write update: a true draft in under a second, the engine's after | Done · #1283 |  |
| P2 | Leave 1:1s out of updates | Done · #1276 |  |
| P3 | The Now wing: where it stands in ten seconds | Done · #1350 | Recovered meeting source chips; populated head facts and Now sections observed on an isolated hub at 1440/393. |
| P4 | Projects and Decisions in Go; withhold dead verbs | Done · #1349 | State/reason in Projects, truthful Not read, scoped Write update in Search. |
| P5 | Sources in one go | Done · #1377 | Paste keeps exact site/account; Found adds meetings and notes together; existing-project sources use the same Door. |
| P6 | Nudge and Ask, in their homes | Done · #1377 | Exact destination and stored action feed Send; shared Ask keeps project scope. |
| P7 | The update is an automation; the steward folds in | Done · #1395 | Manual first; Friday uses the same record. |
| P8 | The agent writes the update | Done · #1395 | Project-scoped Work tools; owner draft preserved; exact result adopted once. |
| P9 | One decision record | Done · #1404 | Admitted canonical record, About/Why, same-ID Project/Decisions/Meeting/Confirm loop. |
| P10 | Watches tell the truth underneath | Done · #1399 | Runnable actions only; observations need no pending effect; MCP uses shared services. |

## Agents (`agents/RECIPE.md`): 16 of 16

| Slice | What | State | Note |
|---|---|---|---|
| AG0 | Tell the truth about state | Done · #1262 |  |
| AG1 | One name: Agents; park the other faces | Done · #1292 |  |
| AG2 | One press to answer and to allow | Done · #1295 |  |
| AG3 | The desk's own answers are visible and in the right form | Done · #1333 |  |
| AG4 | Hand to agent from where the work is | Done · #1334 |  |
| AG5 | Working at once, and a queue | Done · #1308 |  |
| AG6 | Resume after a restart | Done · #1310 |  |
| AG7 | Screen rules (the herdr port) | Done · #1348 | Gaps fixed in #1360; real-agent screen proof remains open. |
| AG8 | The Agents list is the fleet | Done · #1357 | Gaps fixed in #1360; phone Dock decision remains open. |
| AG9 | Agents in Today and Needs you; Done notifies | Done · #1361 |  |
| AG10 | The Result of a turn | Done · #1367 | Recovered local fixes supersede #1364; real hub/fake-agent Result and Terminal walked at 1440/393. |
| AG11 | Agents that work together (MCP) | Done · #1369 | One owned helper, pinned waits, question-only answer, Secure owner Allow, nested rows. |
| AG12 | Review by (builder and reviewer) | Done · #1385 | Bounded two-round pair; durable Result and read-only reviewer authority. |
| AG13 | A HoldSpeak skill | Done · #1374 | Packaged skill, native launch discovery and Connect install; offline Codex discovery observed. |
| AG14 | Automations that hand work to agents | Done · #1402 | Do Hand; native With; compatible Review; durable schedule/event authority and once-only queue. |
| AG15 | Agents he started himself (decision 1) | Done · #1392 | Own native tmux agents show state and accept owner answers/approval; rig discovery stays off. |

## Daily and Needs you (`daily/RECIPE.md`): 11 of 11

| Slice | What | State | Note |
|---|---|---|---|
| D0 | Every row knows its person, its direction and its date (backend) | Done · #1264 |  |
| D1 | One number, true labels | Done · #1277 |  |
| D2 | Needs you: the filters and one verb per row | Done · #1291 |  |
| D3 | Promises from a meeting (owner decision 1) | Done · #1296 |  |
| D4 | Today is one page | Done · #1303 |  |
| D5 | Retire the Brief and The week windows | Done · #1336 |  |
| D6 | People from his work | Done · #1312 |  |
| D7 | The 1:1 prep | Done · #1313 |  |
| D8 | Notices only for what needs him (owner decision 2) | Done · #1340 | Initial notice work #1337; remaining notice work #1340. |
| D9 | Morning prep (after Automations A2–A6 and MCP M1; owner decision 3) | Done · #1342 |  |
| D10 | MCP parity | Done · #1372 | Declared Today read composes the face producers; Decide and People writes retain owner authority. |

## Setup and Settings (`setup/RECIPE.md`): 10 of 10

| Slice | What | State | Note |
|---|---|---|---|
| ST0 | Tell the truth | Done · #1261 | #1261 was "part 1" (speech never wired to a chat server; Voice says if speech works). |
| ST1 | One home each: Rhythm, Wallpaper, Calendar, the engine line | Done · #1347 | Recovery adds phone stepper value geometry fix; two-size real browser check fails before and passes after. |
| ST2 | Accounts that say Works, and Check that does not move acli | Done · #1346 | Stub-backed Jira/Confluence restoration, Found/Use and Remove/Undo; restoration failures stay degraded. |
| ST3 | Setup is one window of found things | Done · #1384 | One found-things window for first run and later Setup; typed microphone recovery stays in place. |
| ST4 | Use everything found, and the look on his network | Done · #1384 | Use selects real engine IDs and the Everything-else assignment; speech remains separate. |
| ST5 | Your people in Setup | Done · #1384 | People use the existing admission producer and report its actual result. |
| ST6 | Let my agents use HoldSpeak | Done · #1388 | Native user-scope tools, hooks and skill; per-agent readback and owned-binding removal in Setup. |
| ST7 | Settings is one page | Done · #1391 | Eight sections; preserved writers and aliases; Engines opens its own window. |
| ST8 | Sign in without a terminal | Done · #1398 | Native provider sign-in runs in the Accounts row; existing Check confirms the result. |
| ST9 | Setup from the terminal and by asking | Done · #1393 | CLI and MCP share the Setup inventory and Use producer; agents read status, adoption requires the owner. |

## Desk shell (`shell/RECIPE.md`): 9 of 10

| Slice | What | State | Note |
|---|---|---|---|
| S0 | Menus and Search show only what works | Done · #1257 |  |
| S1 | Go lists every app | Done · #1259 |  |
| S2 | The New list, the HoldSpeak menu and the keyboard sheet | Done · #1390 | Seven shared New kinds; real Drawer naming at both sizes; setup menu and grouped keys. |
| S3 | The Dock: five daily apps with their state; the keys follow it | Done · #1394 | Manifest order, visible phone words, producer states and matching keys. |
| S4 | The floor holds what he keeps | Done · #1405 | Floor and meeting Keep #1400; person Keep/Remove and mode Search adapters verified with S5. |
| S5 | Search is the command line | Done · #1405 | Ranked results, recent opens, exact About, live object verbs and hub-backed Builder tools. |
| S6 | Wallpaper has one home | Done · #1407 | One Settings Desk home; readable Jupiter label plates. |
| S7 | Windows open where he can see them, at the size of their content | Done · #1407 | Content sizes and reachable heads; remembered collision reseating preserves owner resize. |
| S8 | The Window menu | Done · #1407 | Arrange front/all preserve size and order; exact owner geometry survives reopening. |
| S9 | Ask can arrange the desk (gated) | Part · #1413 | Real LAN opens and tiles the canonical windows; Wrote/Undo restores them. First strict tile 16.27 s exceeds the 10 s gate. |

## Send (`send/RECIPE.md`): 7 of 8

| Slice | What | State | Note |
|---|---|---|---|
| S1 | Tell the truth (small repairs, no new face) | Done · #1268 |  |
| S2 | The first real sends (on his desk, his press) | Open |  |
| S3 | Ready to send in Needs you (owner decision 1) | Done · #1411 | Owner-only Needs membership, original-operation retry and frozen preview; actual 1440/393 prepare/send/discard proof. |
| S4 | What goes out (owner decision 3) | Done · #1411 | Summary and Follow-ups use current confirmed words; frozen Markdown and safe email/plain text. |
| S5 | The Send sheet | Done · #1411 | One in-place sheet, visible Send footer, inline destination, Back focus and durable Sent at both widths. |
| S6 | Edit before Send | Done · #1411 | Edit opens a Note copy; stored changes send to the same destination while the source stays unchanged. |
| S7 | Automations put their result in a destination | Done · #1411 | Completed automation prepares once with its name; actual owner Send preserves exact frozen bytes. |
| S8 | "Not checked yet" warns (owner decision 2) | Done · #1403 | Published unchecked words stay sendable; warning and receipt survive readback. |

## Capture (`capture/RECIPE.md`): 12 of 12

| Slice | What | State | Note |
|---|---|---|---|
| C1 | Talk never freezes the desk | Done · #1255 |  |
| C2 | A summary tells only what came before | Done · #1258 |  |
| C3 | Import asks when it was | Done · #1271 |  |
| C4 | Meeting plugins run on Engines | Done · #1275 |  |
| C5 | The meeting prepares its Results | Done · #1356 | Prepare/Write again #1358; summary publishes before drafts #1359. |
| C6 | Since last time | Done · #1344 |  |
| C7 | One home for recording | Done · #1363 | Record wing, schedule outcomes, Needs you Record now and orb hold. |
| C8 | Speak and Capture in plain words | Done · #1363 | Plain receipts and captured speech handed to the saved note path. |
| C9 | A clean audio callback | Done · #1379 | Callback queue, accepted-byte flush and saved capture failures; hardware walk remains separate. |
| C10 | Meetings record in their own process (decision 1) | Done · #1382 | Child owns native streams and journal; bounded Stop confirms exit before releasing the floor. Hardware acceptance remains open. |
| C11 | Voice commands run desk verbs (decision 3) | Done · #1386 | Closed owner desk verbs; spoken Stop reaches the real recording controller without taking its capture claim. |
| C12 | The glyph tells the truth | Done · #1387 | Recording time and Stop in the native menu bar; lost desk state disables Stop. Native rendering remains owner acceptance. |

## Programs (`programs/RECIPE.md`): 0 of 18

| Slice | What | State | Note |
|---|---|---|---|
| PG1 | The record: Programs, Steps, Checkpoints | Shipped #1602 (2026-10-28) |  |
| PG2 | The control ladder and core questions | Shipped #1602 (2026-10-28) |  |
| PG3 | The gate: a verified log | Shipped #1602 (2026-10-28) |  |
| PG4 | The tick, the hand kind and the brief | Shipped #1602 (2026-10-28) | Ticks every 30 s and after a press; not on a coder frame (PG12). |
| PG5 | Review, findings, the PR and the merge | Shipped #1602 (2026-10-28) | YOLO's third round reuses the worktree (design, Built). |
| PG6 | The handover note, Decided for you and Overturn | Shipped #1602 (2026-10-28) |  |
| PG7 | The desk's tools: REST, MCP and the frame | Shipped #1602 (2026-10-28) | 15 routes, 12 tools; 301 tools in 51 families. |
| PG8 | The Program in the ecosystem, hub half | Shipped #1602 (2026-10-28) |  |
| PG9 | The Programs window and the Program window | Shipped #1602 (2026-10-28) | No race shot (no race fixture). |
| PG10 | The seams on the faces | Shipped #1602 (2026-10-28) | Person line, Room fold, Note verb pinned in app tests only. |
| PG11 | The documents | Shipped #1602 (2026-10-28) |  |
| PG12 | Tick on the coder frame | Open |  |
| PG13 | The Program's level drives the desk's answers | Shipped (2026-10-29) | PG13b: the launch flags and a helper follow the level too; the words say YOLO. Per-step levels are left. |
| PG14 | Automations run a program | Open |  |
| PG15 | Start a program on a call | Open |  |
| PG16 | Decisions from a Program | Open |  |
| PG17 | The first Program is the engine's own history | Open | On his desk. |
| PG18 | Programs on Today | Open |  |

**PG-REQ** (open, 13 slices REQ1–REQ13, lanes HUB/FACES/DOCS, one PR from `lane/programs-requirements-build-20261031`): requirements as a noun, browse and adjust; design `programs/PROGRAMS-REQUIREMENTS-2026-10-31.md` (#1664), canvas `programs/canvases/programs-requirements-2026-10-31.html`, recipe `programs/RECIPE.md` "PG-REQ".

| Slice | What | State | Note |
|---|---|---|---|
| REQ1 | The table, rows, require / edit / waive, the wire | Built (PG-REQ PR) | SCHEMA_VERSION 88. |
| REQ2 | Check and shot kinds at CHECK, the verifier's requirement form | Built (PG-REQ PR) |  |
| REQ3 | The reviewer's REQ lines, UNMET as a REQUIRED finding, one re-ask | Built (PG-REQ PR) |  |
| REQ4 | The gate and the rules, Your word, the end check | Built (PG-REQ PR) | End-check Review is his word until a reviewer runs over the base diff. |
| REQ5 | "What must be true" in the brief, amendments | Built (PG-REQ PR) |  |
| REQ6 | Templates' requirements, the repository's defaults | Built (PG-REQ PR) | Review defaults plant only on reviewed templates; `ux_canon_scan` not planted. |
| REQ7 | Adjust: change, insert before, move, amend, the frozen table | Built (PG-REQ PR) |  |
| REQ8 | REST, MCP, the frame, list filters, fixtures | Built (PG-REQ PR) | 3 new tools (310 in all), 7 new routes. |
| REQ9 | The Programs list: Find, Project, Person, Group, Met | Shipped #1665 (2026-10-31) | `web/src/desk/programs/Requirements.tsx`. |
| REQ10 | The Requirements board, Add requirement, Your turn kinds | Shipped #1665 (2026-10-31) | `web/src/desk/programs/Requirements.tsx`. |
| REQ11 | The step fold, the per-step Ledger, adjust in place | Shipped #1665 (2026-10-31) | `web/src/desk/programs/Requirements.tsx`. |
| REQ12 | The shot pullout and the evidence thumbnail | Shipped #1665 (2026-10-31) | `web/src/desk/programs/Requirements.tsx`. |
| REQ13 | The documents | Built (PG-REQ PR) | `docs/programs.md`, the skill, RECIPE, UX-CANON, STATUS. |

**PG-LANG** (open, 15 slices LANG1–LANG15, lanes HUB/FACES/DOCS, a PR per slice in the fast cycle; first slice on his desk = LANG1 + LANG2): the Program text (a line view that round-trips with the tables), shaping by sentence and voice, planning inference, interview rounds, sizing for small-context engines, the Dreaming template, Delivery Workbench at link and Done only, the SDK; design `programs/PROGRAM-LANGUAGE-2026-10-31.md`, canvas `programs/canvases/program-language-2026-10-31.html` (shaping S-A, rounds R-A), journeys `programs/PROGRAM-JOURNEYS-2026-10-31.md`.

| Slice | What | State | Note |
|---|---|---|---|
| LANG1 | The text: parse, print, diff; `program.text` get and apply with the shown diff; refusals | Shipped #1668 (2026-10-31) | `holdspeak/services/program_text.py`. |
| LANG2 | The Text view beside the board, TextPane, ChangeWell and DiffRow in the kit | Shipped #1670 (2026-10-31) | Board · Text; no "Both" view. |
| LANG3 | Shaping: quick forms, `program.shape` on `agent.plan`, the guard, YOLO apply and Overturn | Shipped #1673 (2026-10-31) | No quick forms: every sentence goes to the engine. |
| LANG4 | The shaping bar (typed) and the landing | Shipped #1673 (2026-10-31) | `ShapeBar.tsx`. |
| LANG5 | Voice: the `program` grammar, the call's held `program.shape` | Shipped #1675 (2026-10-31) | No `program` voice grammar (no caller). |
| LANG6 | Planning: `program.draft`; Run as a program plans | Shipped #1676 (2026-10-31) | `program.plan_draft`. |
| LANG7 | The planning draft face | Shipped #1676 (2026-10-31) | `PlanDraft.tsx`. |
| LANG8 | Sizing: `budget`, the estimate, `step_too_big`, the split | Open | `budget` field #1671, estimate #1676; dispatcher refusal and split by level open. |
| LANG9 | Interview rounds, hub | Shipped #1680 (2026-10-31) | Fields #1671. Rounds never gate Start. |
| LANG10 | The round strip and the question row | Shipped #1680 (2026-10-31) | `Rounds.tsx`. |
| LANG11 | The Measure kind; walk lines on Your word | Open | Kind and walk lines #1671; the verifier open. |
| LANG12 | Dreaming: template, night, within, backlog, digest | Open | `night`, `within` stored #1671. |
| LANG13 | Delivery Workbench: link and the Done PR | Open | `delivery dw` stored #1671. |
| LANG14 | The SDK: Python client and `holdspeak program` CLI | Open |  |
| LANG15 | The documents | Shipped (PG-DOCS-2 PR) | `docs/programs.md`, the skill, RECIPE, UX-CANON, STATUS. |

**PG-JOURNEYS** (open, 14 slices JRN1–JRN14, lanes HUB/FACES/PHONE, a PR per slice after the LANG slice each follows): eight modeled journeys (J1 two paragraphs to a shipped change, J2 the dreaming program, J3 shaping by voice, J4 from the desk for a person, J5 the race, J6 the Phone and the Line, J7 a reviewer-only program, J8 teaching the engine), reconciled with PG-LANG; "What the journeys demand": 24 New, 23 In PG-LANG, 20 exist, 3 dropped. Design `programs/PROGRAM-JOURNEYS-2026-10-31.md`, slices in `programs/PROGRAM-LANGUAGE-2026-10-31.md` §13b, canvas `programs/canvases/program-journeys-2026-10-31.html` (storyboards J1, J2, J3, J6; the interview round, direction A = PG-LANG R-A).

| Slice | What | State | Note |
|---|---|---|---|
| JRN1 | The draft proposes several Programs | Open | After LANG7. |
| JRN2 | Add to tonight: the dreaming backlog mark | Open | After LANG12. |
| JRN3 | The red-main hold for a night | Open | After LANG12. |
| JRN4 | The night's end reaches him on the phone | Open | After LANG12. |
| JRN5 | A spoken answer becomes a prepared answer | Open | After LANG5; the default, no ruling. |
| JRN6 | The item's verbs on a phone message | Open | After LANG5. |
| JRN7 | `program.decide` behind a spoken yes | Shipped #1679 (2026-10-31) | Built as PG-DIRECTION DIR8. |
| JRN8 | The Audit template | Open |  |
| JRN9 | Findings filed as Door tasks; the Findings board | Open |  |
| JRN10 | A proposed fix program from findings | Open |  |
| JRN11 | The lesson rule and the Lesson row | Open |  |
| JRN12 | Keep a lesson for the repository | Open |  |
| JRN13 | Run as a program on a project action row | Open | With LANG6. |
| JRN14 | The person gate's requirements and comments | Open | With LANG6. |

**PG-DIRECTION** (open, 12 slices DIR1–DIR12, lanes HUB/FACES/DOCS, a PR per slice in the fast cycle; first slice on his desk = DIR1 + DIR2 + DIR3, the briefing page over the tailnet with a token, no third party): the owner's ruling 2026-10-31 that calls decide, with context and a free Later; briefing packages (one held item or a digest) for the desk, the Phone app push, a call, Telegram and a tokened page `/b/<token>`; one decision record with `via`; Later with a next touch and the escalation ladder; Settings ▸ Reach. Design `programs/DIRECTION-2026-10-31.md`, canvas `programs/canvases/direction-2026-10-31.html` (page direction A, the brief).

| Slice | What | State | Note |
|---|---|---|---|
| DIR1 | Packages, the token, `/b/<token>` and `/api/b/{token}`, `via` on the ledger | Shipped #1674 (2026-10-31) | First slice. |
| DIR2 | The briefing page (direction A) in the kit, its own entry | Shipped #1674 (2026-10-31) | First slice. |
| DIR3 | The Needs you line and Revoke; Send to my phone ▸ Copy page link | Shipped #1674 (2026-10-31) | First slice. |
| DIR4 | Later everywhere: the words, the Later group, the YOLO provisional park | Shipped #1678 (2026-10-31) | `held_later`, schema 91. |
| DIR5 | Telegram reach: keystore, pairing code, poller, buttons, replies | Shipped #1678 (2026-10-31) | One bot with Cadence. First real pairing untested. |
| DIR6 | Settings ▸ Reach (Notices renamed) | Shipped #1678 (2026-10-31) | `ReachSettings.tsx`. |
| DIR7 | The ladder and the one morning digest (JRN4 folded in) | Open | Telegram rung and a plain digest in #1678. |
| DIR8 | The call that decides (= JRN7); `docs/calls.md` table replaced | Shipped #1679 (2026-10-31) | = JRN7. |
| DIR9 | A Telegram sentence becomes a shaping preview | Open | Telegram half in #1678; the page half open. |
| DIR10 | The other held items as packages | Open |  |
| DIR11 | The documents (`docs/reach.md` and the rest) | Shipped (PG-DOCS-2 PR) | `docs/reach.md` and the rest. |
| DIR12 | Email as a channel | Parked | Until he asks. |

## Phone (`phone/RECIPE.md`): 0 of 16

| Slice | What | State | Note |
|---|---|---|---|
| PH1 | The record and the event log | In the Phone PR |  |
| PH2 | Pairing and the device token | In the Phone PR | No rate limit; 24 random bytes instead. |
| PH3 | Messages, replies and read receipts | In the Phone PR |  |
| PH4 | The call state machine | In the Phone PR | A missed app call falls back to the number. |
| PH5 | Push | In the Phone PR | NullPush until his Apple key; APNs needs `httpx[http2]` (PH13). |
| PH6 | The number transport and answer-later | In the Phone PR |  |
| PH7 | Reach: the rules by control level | In the Phone PR | Only the Programs kinds call it (PH12). |
| PH8 | The desk's tools: REST, MCP, the frame, Needs you | In the Phone PR | 15 routes, 4 tools; 305 tools in 52 families. |
| PH9 | The faces | In the Phone PR | The PH-FACES lane. |
| PH10 | The documents | In the Phone PR |  |
| PH11 | SMS on the number | Open | ai-phone has no SMS. |
| PH12 | The other reach kinds | Open | Heartbeat, aftercare, agent questions. |
| PH13 | The APNs HTTP/2 dependency | Open |  |
| PH14 | The morning release of queued messages | Open |  |
| PH15 | Urgent through Do Not Disturb | Open | Needs Apple's critical-alerts entitlement. |
| PH16 | Today counts the reaches | Open |  |

## The Line (`line/RECIPE.md`): 3 of 8

| Slice | What | State | Note |
|---|---|---|---|
| LINE-1 | The spike and the design | Done #1606 | Measured on the Mac and on karol. |
| LINE-2 | The node | Done #1608 | The runner is unchanged; the Line adapter has AiPhone's methods. |
| LINE-3 | The Line on the home box | Open | The node credential, the units, the build script, `holdspeak line install`. |
| LINE-3b | The Telnyx line | Open | Needs his account; the Number has no settings key yet. |
| LINE-4 | The faces and the docs | Done #1607 (canvas) + the LINE-4b PR | Engines rows are LINE-6. |
| LINE-5 | Barge-in, measured | Open |  |
| LINE-6 | The concierge rows | Open | The Engines catalog is a signed LLM preset envelope. |
| LICENCE | The hub's own GPL pulls (Kokoro, faster-whisper's PyAV) | Open | Needs his ruling. |
