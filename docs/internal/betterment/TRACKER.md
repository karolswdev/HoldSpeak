# Betterment tracker

One row for each recipe slice, with the PR that delivered it. Update this
file in the same PR as `pm/STATUS.md`, after each batch. "Done" means
merged to main. "On his desk" is the backend commit in `pm/STATUS.md`.
Open work that is not a slice is in `FOLLOWUPS.md`.

**Last updated:** 2026-10-21, Ask arrangement and Undo observed; speed gate remains open. Running-desk identity is in `pm/STATUS.md`.

**Total: 115 of 117 slices merged**.
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
