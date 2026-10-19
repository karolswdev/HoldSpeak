# Betterment tracker

One row for each recipe slice, with the PR that delivered it. Update this
file in the same PR as `pm/STATUS.md`, after each batch. "Done" means
merged to main. "On his desk" is the backend commit in `pm/STATUS.md`.
Open work that is not a slice is in `FOLLOWUPS.md`.

**Last updated:** 2026-10-19, recovery includes AG10 #1367 and ST1 #1347. The running desk was last checked at `bfe8bf5dd`; ST1 delivery follows merge.

**Total: 71 of 117 slices merged**, with Send S7 still partial.
Merged means implementation on main; delivery and owner acceptance are tracked separately in `pm/STATUS.md`.
Codex took delivery on 2026-10-19 at the owner's request. See `RECOVERY-2026-10-19.md` for the interrupted worktrees and PRs.

| Cluster | Folder | Done |
|---|---|---|
| Automations | `workbench/` | 11 of 11 |
| Engines | `engines/` | 8 of 8 |
| The desk's tools (MCP) | `mcp/` | 7 of 7 |
| Ask | `asking/` | 10 of 13 |
| Projects | `projects/` | 3 of 11 |
| Agents | `agents/` | 11 of 16 |
| Daily and Needs you | `daily/` | 10 of 11 |
| Setup and Settings | `setup/` | 2 of 10 |
| Desk shell | `shell/` | 2 of 10 |
| Send | `send/` | 1 of 8 |
| Capture | `capture/` | 6 of 12 |

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

## Ask (`asking/RECIPE.md`): 10 of 13

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
| Q8 | One note | Done · #1351 | Phone footer follow-up remains local at 1673f675e. |
| Q9 | Find the tasks | Done · #1354 | Privacy fix #1362 merged; operations/MCP/Edit/Dismiss follow-up #1365 merged. |
| Q10 | Knowledge becomes drawers | Open |  |
| Q11 | Memory where he looks | Open |  |
| Q12 | The Memory app | Open |  |

## Projects (`projects/RECIPE.md`): 3 of 11

| Slice | What | State | Note |
|---|---|---|---|
| P0 | Draft update never freezes the desk and never goes quiet | Done · #1253 |  |
| P1 | Write update: a true draft in under a second, the engine's after | Done · #1283 |  |
| P2 | Leave 1:1s out of updates | Done · #1276 |  |
| P3 | The Now wing: where it stands in ten seconds | Open |  |
| P4 | Projects and Decisions in Go; withhold dead verbs | Open |  |
| P5 | Sources in one go | Open |  |
| P6 | Nudge and Ask, in their homes | Open |  |
| P7 | The update is an automation; the steward folds in | Open |  |
| P8 | The agent writes the update | Open |  |
| P9 | One decision record | Open |  |
| P10 | Watches tell the truth underneath | Open |  |

## Agents (`agents/RECIPE.md`): 11 of 16

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
| AG11 | Agents that work together (MCP) | Open |  |
| AG12 | Review by (builder and reviewer) | Open |  |
| AG13 | A HoldSpeak skill | Open |  |
| AG14 | Automations that hand work to agents | Open |  |
| AG15 | Agents he started himself (decision 1) | Open |  |

## Daily and Needs you (`daily/RECIPE.md`): 10 of 11

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
| D10 | MCP parity | Open |  |

## Setup and Settings (`setup/RECIPE.md`): 2 of 10

| Slice | What | State | Note |
|---|---|---|---|
| ST0 | Tell the truth | Done · #1261 | #1261 was "part 1" (speech never wired to a chat server; Voice says if speech works). |
| ST1 | One home each: Rhythm, Wallpaper, Calendar, the engine line | Done · #1347 | Recovery adds phone stepper value geometry fix; two-size real browser check fails before and passes after. |
| ST2 | Accounts that say Works, and Check that does not move acli | Open |  |
| ST3 | Setup is one window of found things | Open |  |
| ST4 | Use everything found, and the look on his network | Open |  |
| ST5 | Your people in Setup | Open |  |
| ST6 | Let my agents use HoldSpeak | Open |  |
| ST7 | Settings is one page | Open |  |
| ST8 | Sign in without a terminal | Open |  |
| ST9 | Setup from the terminal and by asking | Open |  |

## Desk shell (`shell/RECIPE.md`): 2 of 10

| Slice | What | State | Note |
|---|---|---|---|
| S0 | Menus and Search show only what works | Done · #1257 |  |
| S1 | Go lists every app | Done · #1259 |  |
| S2 | The New list, the HoldSpeak menu and the keyboard sheet | Open |  |
| S3 | The Dock: five daily apps with their state; the keys follow it | Open |  |
| S4 | The floor holds what he keeps | Open |  |
| S5 | Search is the command line | Open |  |
| S6 | Wallpaper has one home | Open |  |
| S7 | Windows open where he can see them, at the size of their content | Open |  |
| S8 | The Window menu | Open |  |
| S9 | Ask can arrange the desk (gated) | Open |  |

## Send (`send/RECIPE.md`): 1 of 8

| Slice | What | State | Note |
|---|---|---|---|
| S1 | Tell the truth (small repairs, no new face) | Done · #1268 |  |
| S2 | The first real sends (on his desk, his press) | Open |  |
| S3 | Ready to send in Needs you (owner decision 1) | Open |  |
| S4 | What goes out (owner decision 3) | Open |  |
| S5 | The Send sheet | Open |  |
| S6 | Edit before Send | Open |  |
| S7 | Automations put their result in a destination | Part | A6 #1322: Put it in can prepare a send to a saved destination. Check the rest of S7 against the recipe. |
| S8 | "Not checked yet" warns (owner decision 2) | Open |  |

## Capture (`capture/RECIPE.md`): 6 of 12

| Slice | What | State | Note |
|---|---|---|---|
| C1 | Talk never freezes the desk | Done · #1255 |  |
| C2 | A summary tells only what came before | Done · #1258 |  |
| C3 | Import asks when it was | Done · #1271 |  |
| C4 | Meeting plugins run on Engines | Done · #1275 |  |
| C5 | The meeting prepares its Results | Done · #1356 | Prepare/Write again #1358; summary publishes before drafts #1359. |
| C6 | Since last time | Done · #1344 |  |
| C7 | One home for recording | Open |  |
| C8 | Speak and Capture in plain words | Open |  |
| C9 | A clean audio callback | Open |  |
| C10 | Meetings record in their own process (decision 1) | Open |  |
| C11 | Voice commands run desk verbs (decision 3) | Open |  |
| C12 | The glyph tells the truth | Open |  |
