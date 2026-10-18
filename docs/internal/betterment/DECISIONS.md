# Decisions for the owner, one page

**ADOPTED 2026-10-17: the owner answered "defaults". Every default below
is now a ruling.**

Every decision from the plan and the eleven designs. Each one has a
recommended default, so building can start on the default. Answer
"defaults", or name the numbers you want to change.

## The plan (`PLAN.md`)

| # | Decision | Default |
|---|---|---|
| 1 | Adopt the product model: one name and one home for each concept (Note, Ask, About, Automation, Agent, Engine, Result, Needs you, Today, Person, Project, Decision, Send, Settings) | yes |
| 2 | Automations absorbs Workflows, Reactions, Resourceful, Rhythm's loops and saved personas. Data and MCP tools stay. | yes |
| 3 | "Agent" means only a coding agent session (Claude Code, Codex, pi) | yes |
| 4 | Run the live flag check (MCP M0) with your real `claude`, `codex` and `pi`: one short prompt each, a few cents | yes |

## Automations (`workbench/`)

| # | Decision | Default |
|---|---|---|
| 5 | A result is not a review: it is NEW until opened, with no "awaiting review" | yes |
| 6 | Take "New Workflow", the Agents list and idle starts off the face | yes |
| 7 | An agent engine may read a repository folder (read-only) for an automation | yes, last slice |

## Engines (`engines/`)

| # | Decision | Default |
|---|---|---|
| 8 | Replace the drag-a-wire switchboard with the "What runs where" list | yes; the switchboard goes behind RAW |
| 9 | Anthropic as a service: try Anthropic's OpenAI-compatible endpoint first | yes |
| 10 | Spend limit per engine and per automation | No limit, cost shown on each result |

## The desk's tools (`mcp/`)

| # | Decision | Default |
|---|---|---|
| 11 | Automation runs get the CONDUCTOR set: reads (People included) and desk writes; no send, config or authority | yes |
| 12 | Only HoldSpeak's server inside a run. Gmail, Drive, Calendar and pixellab stay out. | yes |
| 13 | No nested model tools inside a run | yes |

## Asking (`asking/`)

| # | Decision | Default |
|---|---|---|
| 14 | Every Ask is kept as a thread, with no Keep or Bin | yes |
| 15 | Knowledge collections become drawers, and New Knowledge leaves the New list | yes |
| 16 | Ask may write on the desk when you ask it (tasks, notes, proposed decisions), with Undo. Sends are only prepared. | yes |

## Projects (`projects/`)

| # | Decision | Default |
|---|---|---|
| 17 | The Friday update is an Automation, and the steward folds into Automations and Needs you | yes |
| 18 | Updates leave out 1:1s and People notes unless you add them | yes |
| 19 | One decision record and one home (Decisions) | yes |

## Agents (`agents/`)

| # | Decision | Default |
|---|---|---|
| 20 | See agents you started yourself in tmux (read locally) | yes |
| 21 | A finished agent notifies you quietly and stays NEW until opened | yes |
| 22 | A launched agent may start one helper without your press (Normal and YOLO; Secure asks) | yes |
| 23 | Agents working at once: a setting, default 6 (today a fixed 3), and finished agents stop counting | yes |

## The daily surface and People (`daily/`)

| # | Decision | Default |
|---|---|---|
| 24 | Promises from a meeting are kept on arrival, each with Drop and Undo; decisions still wait for Decide | yes |
| 25 | Finished work notifies quietly and never counts in Needs you | yes |
| 26 | Morning prep (weekdays 7:30) is on by default once a tool-capable engine exists | yes |

## Setup (`setup/`)

| # | Decision | Default |
|---|---|---|
| 27 | "Use everything found" includes the 144 MB speech model, never the 3 GB local model | yes |
| 28 | Setup looks on your network each time it opens | yes |
| 29 | Your hand-run agents get the desk's tools with your authority, per agent, with Undo | yes |

## The desk shell (`shell/`)

| # | Decision | Default |
|---|---|---|
| 30 | The floor shows only what you keep. The Needs you number lives on the bell, Today and Go, not on a desk icon. | yes |
| 31 | Wallpaper is one Settings row. Quiet Desk is the default; the 11 scenes are opt-in. | yes |
| 32 | The keys follow the Dock: ⌃1 Today, ⌃2 Meetings, ⌃3 People, ⌃4 Agents, ⌃5 Speak | yes |

## Send (`send/`)

| # | Decision | Default |
|---|---|---|
| 33 | Ready-to-send work lives in Needs you | yes |
| 34 | "Not checked yet" warns; it does not refuse | yes |
| 35 | Meetings send confirmed items only | yes |

## Capture (`capture/`)

| # | Decision | Default |
|---|---|---|
| 36 | Recording runs in its own process, so a stuck audio device never freezes the hub | yes |
| 37 | A meeting prepares its drafts (ADR, diagram, stakeholder update) by itself after the summary | yes |
| 38 | Voice commands can run five desk verbs, never Send, settings or authority | yes |

## Building now: truth fixes that need no decision

These slices repair things that are broken or that report wrong facts. No
answer above changes them, so they start at once:

- Automations **A0** (run records, failure reasons, the schedule switching
  itself off, Re-run)
- Asking **Q0** (silent empty Thread replies), **Q1** (the Room's Ask
  failure words), **Q2** (a question goes ahead of background work)
- Projects **P1** (an instant draft from records), **P2** (1:1s leak into
  updates)
- Agents **AG0** (Done/New state, Stopped by restart, the silent YOLO
  answer)
- Daily **D0** (each row gets its person, direction and real date), **D1**
  (one number)
- Setup **ST0** (the first-run press that broke speech, the Voice fact)
- Shell **S0** (menus show only what works), **S1** (Go lists every app)
- Send **S1** (account status, the GitHub save, SENDING forever)
- Capture **C1** (Talk off the event loop), **C2** (summaries read only
  earlier sources), **C3** (Import asks the date), **C4** (plugins run on
  Engines)
