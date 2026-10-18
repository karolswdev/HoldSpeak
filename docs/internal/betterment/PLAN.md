# The betterment plan

Owner, 2026-10-17: "I want you to have a much more comprehensive plan." And:
"This shit's supposed to be the most advanced Agentic OS in the world."

This is the master plan. It covers every feature (`INVENTORY.md`: 45
features in 10 clusters), the product model that every design obeys, the
order of the design waves, and the build tracks that run alongside them.

## 1. What is wrong, across the whole product

The inventory shows one root cause that sits above every single feature:
**one job, many homes, many names.**

- "Do this for me later or again": Workbench, Workflow, Sequence, Reactions,
  Resourceful, Rhythm's loops (five concepts).
- "Ask my work a question": Ask AI, Ask this project, Object ▸ Ask, Develop
  this thought, Thread (five places, each with its own grounding words).
- "What needs me": Needs you, Follow-through, Today ▸ To decide, The week,
  the Room's "needs me now", People ▸ They owe you (six faces).
- "Agent": a saved persona, a coding session, a Workbench word, an MCP
  client (four meanings).
- Note and Thought, two Briefs, two Rhythms, two Wallpapers, Engines under
  four names.
- Ten tools that only Search can reach, because Go ▸ Tools is never drawn.

A feature-by-feature polish would make the sprawl prettier. So the plan
starts with the product model, then designs each cluster inside it.

## 2. The product model (rulings every design obeys)

One name and one home for each concept. A cluster design may challenge a
ruling in its §5 decisions, but must not ignore it.

| Concept | The one name he sees | Its one home | What it absorbs |
|---|---|---|---|
| Anything he writes or says to keep | **Note** | Notes (drawers on the desk) | Thought, seed notes |
| A question to his work | **Ask** (the verb). Its answer can go on as a **Thread** (the conversation). | The Ask/Thread window, opened pre-scoped from anywhere | Ask AI, Ask this project, Object ▸ Ask, Develop this thought |
| What a question or job is about | **About** (named chips: meetings, notes, people, projects, drawers, folders) | The same picker in Ask, Thread and Automations | grounding, refs, zones, context |
| Work done again or later | **Automation** (When · Do · About · With · Put it in) | Automations | Workbench, Workflow, Sequence, Reactions, Resourceful, Rhythm's loops, prepared recipes, saved personas ("New Agent") |
| A coding agent session | **Agent** (Claude Code, Codex, pi) | Agents (today Conductor) | Conductor sessions, Hand to agent |
| What runs AI work | **Engine** | Engines | Runs on, Concierge, Models |
| What a run produces | **Result** (with Looked at · Wrote · Prepared) | On the automation or agent, and in Today while NEW | artifacts, receipts, outputs |
| Everything waiting on him | **Needs you** | One list; Today shows its top | Follow-through, To decide, The week's asks, the Room's needs-me, They owe you (these become filters of the one list) |
| Start of the day | **Today** | Today | Brief window, Intelligence, Monday brief (a Monday section of Today) |
| His reports and peers | **Person** | People | — |
| A body of work | **Project** | The project's window (the Room) | — |
| A thing decided | **Decision** | Decisions | Meeting "Decided", Today ▸ Decisions (they link, they do not keep a copy) |
| Anything leaving the machine | **Send** | The Send well; he presses Send | — |
| Configuration | **Settings** | Settings | the second Rhythm and Wallpaper homes |

Shell rulings:

- **Go lists every app.** No app is reachable only by Search. Builder tools
  (Activity, Processes, Components, Context, Calendar snapshot) live behind
  RAW, not in Go.
- **Every AI feature runs on Engines**, and every tool-capable engine gets
  the desk's tools (`mcp/DESIGN.md`).
- **Every verb on the face has an MCP tool**, so that an agent can do what
  he can do, under the same press rules (egress, authority and config stop
  for him).
- **One chip style, one material, the library Button** (UX-CANON).

## 3. The design waves

Each cluster gets the treatment Automations got: a live walk, a code map,
a design and a recipe (`CLUSTER-BRIEF.md`). Workers draft, and the
orchestrator reviews and rewrites. Each design merges to main when it is
ready.

| Wave | Cluster (INVENTORY rank) | Folder | Includes | State |
|---|---|---|---|---|
| 0 | G. Automation (1) | `workbench/` | Workbench → Automations; Workflows, Reactions and Rhythm's loops fold in | drafted |
| 0 | H. Engines (part of 4) | `engines/` | Engines, agent CLIs, What runs where | drafted |
| 0 | The desk's tools | `mcp/` | CONDUCTOR set for runs; MCP parity | drafted |
| 0 | Agents vs herdr | `herdr/STUDY.md` | state on the desk, hand-offs, resume, fleet | studied |
| 1 | E. Asking, thinking and memory (2) | `asking/` | Ask, Threads, Notes, Knowledge, Memory, Search | — |
| 1 | C. Projects, updates and decisions (3) | `projects/` | Room, New Project, Draft update, Steward, Watches, Decisions | — |
| 1 | F. Agents (5) | `agents/` | Conductor, Hand to agent, Agents, Delivery board, plus the herdr ideas | — |
| 1 | D + B. The daily surface, People and commitments (6, 7) | `daily/` | Today, Brief, Needs you, The week, Notifications, People, Follow-through | — |
| 2 | H. Settings and setup (rest of 4) | `setup/` | Settings, Accounts, First run | — |
| 2 | I. The desk shell (10) | `shell/` | Windows, Menus, Dock, Desk and drawers, Wallpapers, Builder tools | — |
| 2 | J. Delivery and send (8) | `send/` | Send to, destinations, real sends | — |
| 2 | A. Capture (9) | `capture/` | Speak, hotkey, Voice commands, Meetings, Record, Scheduled recording | — |

Wave 2 starts when the first wave-1 design is reviewed, not when the whole
of wave 1 is done.

## 4. The build tracks (they run while design goes on)

Build starts on a cluster as soon as its design is settled. Recipes cross
clusters, so these are the tracks in order:

| Track | Slices, in order | Starts |
|---|---|---|
| T1 Engines + tools | MCP M0 (live flag check, owner's OK) → Engines E1 + MCP M1 → E2 → E3 → E4 → E5 → E6 → E7; MCP M2, M4, M5 | now (after M0) |
| T2 Automations | A0 (tell the truth) → A1 (name, Go) → A2 → A3 → A4 → A5 → A6 → A7 → A8 → A9 → A10; MCP M3, M6 | A0 and A1 now |
| T3 Shell quick fixes | Go ▸ Tools drawn (every app in Go), parked rows unmapped, Settle in removed, Brief window retired, seed notes moved | now; small, from INVENTORY §3 |
| T4 Wave-1 recipes | from `asking/`, `projects/`, `agents/`, `daily/` | as each design settles |
| T5 Wave-2 recipes | from `setup/`, `shell/`, `send/`, `capture/` | as each design settles |

Every slice follows the fast cycle: quick check, then merge; the main
watcher runs the whole suite; Astra reviews after the merge.

## 5. Decisions for the owner (the plan level)

1. **The product model in §2.** Recommended: adopt it as written. Each
   cluster design applies it.
2. **Automations absorbs Workflows, Reactions, Resourceful, Rhythm's loops
   and saved personas.** Their data and MCP tools stay, and nothing is
   deleted. Recommended: yes.
3. **"Agent" means only a coding agent session.** "New Agent" (saved
   personas) is retired as a face concept. Recommended: yes.

## 6. How we know the plan worked

He uses HoldSpeak for a full working week for his real job: his meetings,
his three people, his projects and his Friday update, with his engines. He
hits no wall that sends him to us. Each cluster's §6 test passes on his own
desk.
