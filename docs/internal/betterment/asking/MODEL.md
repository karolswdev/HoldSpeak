# Asking, thinking and memory: the code map

Read from `main` (`68e49a296`) on 2026-10-17. Paths are from the repository
root. The walk that goes with it is `RECON.md`.

## 1. Ask

**In data.** The Ask window stores nothing while it runs. Its states live in
the browser only: `compose | routing | printed`
(`web/src/desk/components/AskPanel.tsx:108`); a failure goes back to
`compose` (`:290-293`). A finished answer is a row in `ask_results`
(`holdspeak/db/schema.py:2377-2384`). Only the Room's asks are durable, in
`project_ask_tasks` (`schema.py:4638-4660`), with the states `saved, running,
waiting, failed, incomplete, accepted, discarded`.

**One run** (`AskService.ask`, `holdspeak/services/ask_service.py:186-466`;
MCP `ask.run` in `holdspeak/mcp/families/ask.py:111-130`):

1. Material: the bodies of the picked notes, artifacts and meetings, cut at
   6000 characters (`_assemble_material`, `:693-707`). A Knowledge collection
   gives only its member ids (`:705`). A project gives nothing: there is no
   project branch (`:700-707`).
2. Grounding: meeting ids, artifact ids, refs, `expand`, at most 16 refs
   (`_grounding`, `:802-842`; `GROUNDING_MAX_REFS`, `web/src/desk/grounding.ts:26`),
   plus memory recall and memory pages (`:223-235`, `:824-833`). With nothing
   picked, it expands to the desk; that is the `GROUNDED ON 14 OF 14` of
   `RECON.md` step 4.
3. Prompt: one system line, "You are the desk's AI core…" (`:33`), then the
   question, the material and the grounding (`:236`). **No tools.** The payload
   has no `tools` key (`:256-267`, `:432`).
4. Engine: capability `ask.answer` when it is routed (`:243-248`), else the
   legacy placement (`:389-420`). Deadline 60 s (`:438`); the routed policy
   `retry.text.standard` is 60 s with 2 attempts per entry and 4 in all
   (`holdspeak/inference_capabilities.py:1235`). Two attempts of 60 s is the
   122 s of Recon R1 and the 100 s of `RECON.md` step 8.

**Failure words.** `runAsk` keeps a `reason` code and falls back to
`did_not_answer` when the hub sends none (`web/src/desk/ask.ts:264-267`). The
Ask window prints only the words for that code
(`web/src/desk/surface/runWords.ts:17-27`): "No engine for answers", "Engine
busy", "… did not answer", "Timed out after N s". The old catch-all
`THE HUB REFUSED IT` was removed on 2026-10-13 (commit `4cc536080`). What is
left: every `ValidationError` and every unmapped code (`grounding_not_found`,
a mesh node offline, `model_not_advertised`) prints "… did not answer",
although nothing reached the engine. The Room prints the hub's raw sentence
instead (`web/src/features/project-room/ProjectRoomCore.tsx:2141`), which is
how the SQL error of `RECON.md` step 9 reached the face.

**Keep.** `ask.keep` writes an **artifact** of type `plugin_output`, plugin
`web.desk`, `via_kind: "ask"` (`ask_service.py:664-691`, `:847-852`), and the
window opens it (`AskPanel.tsx:341-347`). The artifact face titles it with the
plugin label, which is why it reads `Summarize`. Nothing turns an Ask into a
Thread.

## 2. The five Ask doors

| Door | Where | What it calls | Its scope words |
|---|---|---|---|
| Ask AI (Go, ⌘I) | `web/src/desk/applications.ts:105-114`; `web/src/desk/verbRegistry.ts:692-702` | AskPanel → `POST /api/ask` | "Ask about your work", `ADD NOTES`, "Ground on the rails", `Question sources:` |
| Object ▸ Ask AI | `verbRegistry.ts:485-503` | the same panel, with the selection | `Question sources:` |
| Object ▸ Ask this project | `verbRegistry.ts:450-468` | the same body as Ask AI | sends `project:<id>` as context, which the hub ignores (§1, step 1) |
| Room ▸ Ask this project | `ProjectRoomCore.tsx:2069-2160` | durable `project_ask_tasks`, then `runAsk` with `refs:[project:id]` | `Ask this project…`, `ANSWER`, `UNFINISHED`, `SAVED HERE`, `Resume` |
| Thought ▸ Ask | `web/src/desk/pullouts/ThoughtWorkspaceWindow.tsx:547-567` | opens AskPanel with the note | "Ask about this note", `Selected text` |
| Thread | `web/src/desk/pullouts/ThreadPullout.tsx` | not Ask: `chat.turn` (§3) | `Sources`, `@`, `Mode` |

`object.ask` and `object.ask-project` have the same body
(`verbRegistry.ts:450-503`); Search has to remove the doubled rows
(`web/src/desk/components/DeskToolShelf.tsx:221-260`).

## 3. Threads

**In data** (`schema.py:3894-4057`): `threads` (the mode is `recipe_id`),
`thread_messages` (user, assistant, system, tool), `thread_message_parts`
(text, reasoning, tool_call, attachment, annotation, guardrail),
`thread_refs` (frozen sources), `thread_tool_policy` (allow, ask, deny).

**Engine.** Capability `chat.turn`, "Desk chat"
(`holdspeak/services/thread_service.py:564-565`;
`inference_capabilities.py:1112`), on its own routing row, apart from
`ask.answer`.

**Tools.** Threads are the only place a model calls tools today. A thread with
no mode gets `CHAT_PALETTE` (`holdspeak/services/thread_tools.py:355-377`),
which includes `memory.search` and `memory.page` and no `kb.*`. Modes
(`holdspeak/services/thread_modes.py:138-187`): Desk (evidence reads), Chase
(plus People and follow-through effects), Draft (none), Plan (thought,
decision and memory reads), Project (none), Interview. Only `work`-class tools
reach a thread (`holdspeak/tool_authority.py:32-38`, `:301`). A held call
offers Allow once, Allow always, Deny (`ThreadPullout.tsx:617-649`). The
desk's default control mode is `yolo` (`thread_service.py:198`), so most
calls run without a hold. Limits: 30 s per tool (`:121`), 10 passes (`:118`).

**The silent empty reply.** In the streaming turn, a pass with no tool calls
takes `outcome` and `error` from the engine's answer
(`thread_service.py:1326-1350`). An error text is made only for Interview
mode. The message is then completed with `error_json` only when there is
error text or an error code (`:1826-1841`). So a failed turn in any other mode
completes as an empty reply with no error. That is what the face showed
twice (`RECON.md` steps 12 and 13). Why the engine call failed is not traced.

**Seed refs are lost.** Object ▸ Continue in thread sends
`seed_refs: [{ref_kind, ref_id}]` (`verbRegistry.ts:543`). The service expects
strings and stores `ref_kind="seed", ref_id=str(dict)`
(`thread_service.py:236-241`). The row has no frozen body, so the model never
sees the object, and the face prints the dict (`RECON.md` step 11).

**Slash commands** (`web/src/desk/components/ThreadComposer.tsx:90-101`):
keep, fork, stop, new, mode, prompt, tools, todo, compact, guardrail. Their
entries in the verb registry are empty placeholders
(`verbRegistry.ts:897-990`). `@` finds meetings, notes, artifacts, decisions
and people only (`ThreadComposer.tsx:442-464`).

**Keep from a thread** makes a note by default, an artifact under More
(`thread_service.py:1988-2050`). **No path creates a thread from an Ask.**

## 4. Notes and thoughts

**One stored kind.** A thought is an ordinary `notes` row plus a
`refinement_thoughts` row that points at it (`working_note_id`) and keeps the
raw first text (`schema.py:886-924`). States: `working, completed,
tombstoned`.

**Two doors, two windows.** Desk ▸ New Note (`verbRegistry.ts:165-179`) makes
a plain note, which opens in `NotePullout` (the form with the format bar).
Desk ▸ Write a thought (⌃T, `:182-196`, `web/src/desk/newThought.ts:49-90`)
makes a note and adopts it as a thought, which opens in
`ThoughtWorkspaceWindow` (the sticky). The window is chosen by ownership
(`web/src/desk/pullouts/Pullout.tsx:152-185`).

**"Develop".** On a plain note, Develop this thought
(`web/src/desk/pullouts/NotePullout.tsx:527`) calls `POST /api/thoughts/adopt`
and runs no model. The model step (`POST /api/thoughts/{id}/refine`,
capability `thought.interview`, `holdspeak/services/refinement_coordinator.py:125`)
is reachable only from the retry row of a failed or busy run
(`ThoughtWorkspaceWindow.tsx:450-476`); an idle thought has no button that
starts it, although the hub offers one (`refinement_thought_service.py:1691-1696`).
NotePullout's own thought branch (`NotePullout.tsx:406-505`) and
`ThoughtContextPicker` cannot be reached in the live app.

**Finish** sets `completed` and writes a receipt
(`holdspeak/services/refinement_thought_service.py:1189-1262`). It extracts
nothing.

**The foot verbs** (`ThoughtWorkspaceWindow.tsx:694-702`): Task
(`TaskWell`, `POST /api/door/items`), Project (`ProjectWell`, a project
resource), Ask (opens AskPanel), Send.

**MCP**: 18 `thought.*` tools (`holdspeak/mcp/families/thought.py:65-201`),
`note.*` for plain notes.

## 5. Knowledge collections

`kbs` (id, name, member_ids_json) and `knowledge_memberships`
(`schema.py:1402-1409`, `:1631`). The ref prefix is `knowledge:`. The editor
adds and removes members (`web/src/desk/pullouts/editors/KbEditor.tsx:34-80`);
the window offers Copy, Dictate about this, Edit and no Ask
(`web/src/desk/pullouts/KbPullout.tsx:71-94`). Ask uses a collection when it
is picked as grounding (members expand, `holdspeak/grounding.py:670-690`).
Threads do not use it. MCP: `kb.add_member`, `kb.remove_member`,
`kb.list_members`. A collection is, in data, a named list of desk objects; a
drawer (`directory`, prefix `zone:`) is the same thing with a place on the
desk.

## 6. Memory and Search

**Memory in data** (`schema.py:4749-5061`): sources, chunks, embeddings,
entities, facts, observations (shown as "beliefs"), pages, jobs. Background
jobs extract facts and fold them into observations; pages are written by
capability `memory.page` from observations and recall, each sentence with its
refs, and read with no model call (`holdspeak/memory/pages.py:1-40`,
`docs/internal/MEMORY-DESIGN.md` §3.4). The fixed set: four pages a project,
two for the desk (`web/src/desk/standingPages.tsx:28-35`).

**Where it shows.** Pages: the Room's Pages fold
(`ProjectRoomCore.tsx:3041-3047`) and the Brief
(`web/src/desk/pullouts/views/BriefView.tsx:191`). The Memory window is
`ProjectMemoryCore`, a re-export of the Room core
(`web/src/pages/cores/ProjectMemoryCore.tsx:5-9`), which with no project draws
the recall face from `/api/memory/recall`. Its manifest row
(`applications.ts:337-353`) has no Go entry, so only Search reaches it.
`web/src/desk/deskMemory.ts` is not Memory: it keeps drafts and window places.

**Search (⌘K)** (`DeskToolShelf.tsx`): local rows, then up to 6 memory rows
from `/api/memory/search` after 3 characters (`:283-288`, `:815-859`), each
with a "found by" word (`KEYWORD`, `MEANING`, `TIME`, `NAME`, `LINK`;
`web/src/desk/components/FoundBy.tsx:14-19`). Memory rows are not in the
first-press object sections (`:213`), so with only memory hits the default
row is a verb or program (`:885-886`). Snippets pass markdown through
(`RECON.md` step 27). No row asks the typed question.

## 7. "About" today: six pickers

| Surface | Picker | Words |
|---|---|---|
| Ask | `GroundingSection`, `RailsPicker` (`AskPanel.tsx:585-605`) | `ADD NOTES` (default label "Ground this ask"), "Ground on the rails", `Question sources:` |
| Thread | `@` and the Sources picker (`ThreadComposer.tsx:1006-1014`, `:1151-1154`) | `Sources`, "Find source" |
| Thought (live) | `ThoughtReadsWell` (`ThoughtWorkspaceWindow.tsx:661`) | `Add a note`, "Reads: …" |
| Thought (dead) | `ThoughtContextPicker` (`NotePullout.tsx:449`) | "AI context", "Use for new Thoughts" |
| Coder steer | the Ask pickers (`web/src/desk/components/SessionPullout.tsx:524-541`) | "Steering sources" |
| Workbench | `@` drawers (`web/src/desk/components/WorkbenchWindow.tsx:1067-1152`) | "Reference assignment" |
| Room | fixed `refs:[project:id]` | none |

## 8. Constraints

- Stored names stay: `notes`, `refinement_thoughts`, `kbs`, `threads` and
  `thread_*`, `ask_results`, `project_ask_tasks` and its state list, the
  `hs-seed-mode-*` mode ids, capabilities `ask.answer`, `chat.turn`,
  `thought.interview`, `memory.page`, and the MCP families `ask.*`,
  `thought.*` (18), `memory.*`, `kb.*`. The user never needs to see them.
- Threads already have the tool loop, the held-call face and the tool
  policy. Ask has none of them. The cheapest road to "ask my whole desk" is
  to let Ask run as a thread turn, not to give Ask its own loop.
- The CONDUCTOR set (`holdspeak/mcp/palettes.py:61-125`) is for launched
  agents; threads use `CHAT_PALETTE` and the mode sets. `../mcp/DESIGN.md`
  ruled that automation runs get CONDUCTOR; Ask should get the same set so
  that the rule is one rule.
