# Status

The one status file. Update it when a PR merges. Rules: `CLAUDE.md`, "How we work now".
The old roadmap under `pm/roadmap/` is history; it is not updated. Its shots and run
dumps are on branch `archive/evidence-2026-10-04` (`pm/ARCHIVE.md`).

**Last updated:** 2026-10-04

## Current phase

None chartered. PHILO Phase 13, The Desk, is complete (18/18 stories, closed 2026-10-03).
Record: `pm/roadmap/holdspeak-philo/phase-13-the-desk/current-phase-status.md`.

Now: the fast-lane change (owner ruling 2026-10-03): remove the commit gate; stop
committing generated docs and line-number test maps; split the tests.

## Open work

Now: finish it all as one onboarding experience (owner 2026-10-05: "I want you to finish it all up"): five fix lanes + one canvas for every face that needs design.

Done: strong defaults, batteries included (owner direction 2026-10-05): #855, #856 and #859 merged: a fresh install now gets local AI from one first-run press. His desk: assign his LAN server as the default (and memory) when his hub next runs.

Now: prepare for the owner's week of real use (assignment 2026-10-03): inventory
(`docs/internal/INVENTORY-2026-10-03.md`), clean up, polish, wire memory into every
process; and the native memory system (`docs/internal/MEMORY-DESIGN.md`, slice 1 merged).

Test state on main (2026-10-05, after #864): FAST 13,846 passed with the #861 fix in; web 3,431 passed, 0 failed. After a batch of merges, run FAST, the web baseline and the scoped browser tests before calling it done.

| Item | Owner | PR |
|---|---|---|
| Memory dates: Kestrel (r09) found only with vectors (strict xfail); live extraction occasionally returns an empty answer (2 of 68 repeats); a one-word capitalised password with no digit ("secret: Hunter") is kept | — | — |
| First run: the browser copy of the needs-you rule (web/src/desk/needsYou.ts) lacks the person-identity guard (no production caller today); physical mic and real model inference not verified | — | — |
| Send folder: six older Send glass rigs park the built-in (direct DB write) to keep their ratified boards; Google Drive / OneDrive provider ids unverified on real installs (fall back to SYNCED); GitHub / Jira offered when signed in (inventory item 9b) not built; inventory item 8 (calendar row at first run) not built | — | — |
| Defaults: the 4B starter's meeting analysis is untested on real hardware; the real faster-whisper fence skips in CI (needs a cached model) | — | — |
| Defaults: never run against a real Ollama/LM Studio/llama.cpp server; a binding disabled and re-enabled between the backlog tick and the claim consumes the mark (manual retry); GitHub Enterprise entry.egress_host says github.com; meeting import does not write the backlog mark; real EventKit prompt/read unverified | — | — |
| Memory faces (need a canvas): the Desk memory card with observations, the standing pages, the ⌘K palette's use of fused recall | Muad'Dib | — |
| Memory: thread rows saved before the origin column ('' origin) that were project hits and later refiled still replay (accepted, Astra #852); Chase has about 440 bytes of palette room at 32k | — | — |
| Memory pages: never run with the real LAN model; no person pages (no non-People key exists for a person scope) | owner | — |
| Memory observations: never run with the real LAN model; no benchmark group; join default search only by naming kind `observation` | — | — |
| Memory facts: never run through the product path with the real LAN model | — | — |
| Memory: summary and topic as their own chunks not built — needs one transition over vectors, facts, observations and pages (MEMORY-DESIGN.md); the Desk memory face does not show the four new kinds | — | — |
| Memory: the agent tool turn (RecipeService.chat → run_recipe) is retired code with no caller; Recipe chat runs as a thread turn whose default tools include memory.search (proved by tests/unit/test_thread_memory_search_live.py). The update draft and Prep are not fitted to a token budget (their path has none) | — | — |
| Memory: live meeting analysis and voice resolve read no memory (a lookup is 100–400 ms against a 50 ms bar) | — | — |
| Memory: the decision-promotion self-recall test passes before the fix; mint through DecisionLifecycleService.promote (Astra, #830) | — | — |
| Memory: not measured on the owner's real desk; new items take up to 120 s to become searchable by meaning | — | — |
| Bus: background writers (calendar ingest, heartbeat sweep, cadence tick) and MCP tools outside the registry send no frame; announcements carry an empty id and op "create" on some routes | — | — |
| Needs you (#872 in review): the shade and palette show a per-Room count; the Chair caption "BRIEF · N THINGS WAITING" is a different count | — | — |
| Times: about 150 writers still store timestamps with no zone; a schedule edited under the old code keeps a wrong time until saved again | — | — |
| Sent Brief: People text stays in old prepared and discarded rows on disk; the re-render check covers the Brief only | — | — |
| The roadmaps read takes 2–3 s on each desk refresh | — | — |
| The Dock overflows at 1440 with five projects (the ratified shelf scrolls; Places and Record go off the right edge): owner's design call pending — recommendation: pin Places and Record; Calendar cannot tell no-vision-model from a failed model (the hub sends one code); Ask shows "GROUNDED ON 0 OF 0" (a counter of zero); older thread rows and task-resume Ask answers show no route lamp | owner / — | — |
| Decisions (housekeeping #867): fold the older ReactionService watch system into WatchService (Workbench automations are its only face); three primitives/decisions routes are unreachable in the hub; six routes have no caller (incl. POST /api/setup/local-ai/cancel); connector_fixtures.py lives in the product package; heartbeat.run_now builds WatchService without the Jira adapter; a test left tmux session hs10605_kill_62847 on the owner's server | owner | — |

## Last merged (newest first)

- #875 — Route in footer (owner pick C): a lamp per Ask/chat turn from its receipt (least private sent attempt; FALLBACK marked); the footer carries the last turn's host, model and its own receipt; failed Asks keep their route; one egress classifier everywhere
- #871 — Memory leftovers: every read tool replays as a re-read stub (classed by its originating call); the routed Thought reflects pages and observations; thread time bounds as instants; dead runners stop holding extraction; secrets are never search keys; hand-attached sources redacted (schema text kept)
- #870 — Memory accuracy: dates by named month and reported tense, both years by tense (EXTRACTOR_VERSION 4, re-recorded live); the initial-alias rule; one cited input must hold every content word of a page sentence; content-hash page staleness
- #869 — Face polish: 393 Dock pages start on a whole item; the Chair reopens at its tile; Roadmap from the palette opens by its own name; honest Calendar tokens; palette matching stays within a word; paths shortened only under the known HOME; Processes names its targets; product words decision/thread/workbench; Roadmap rows no longer overlap at 393
- #868 — Defaults: hub on 8765 with a fallback; doctor's token only to loopback; blank MLX = not set up; a loopback rescan until a default exists; a durable summary backlog for meetings saved with no engine (honours Skip; drains only to a local or owner-chosen engine); the meeting-intel queue follows the global default; onboarding backends (macOS Calendar via EventKit, ICS check, gh/acli detection)
- #867 — Housekeeping: typed MCP errors; long MCP tools run in parallel under per-key locks (atomic open_review / draft_update / watch.test); a PR review after a story edit is a new run; tmux test rig isolated; 1,363 dead lines parked; DB open about twice as fast; nightly tmp space fixed
- #864 — Built-in "HoldSpeak folder" Send destination (~/Documents/HoldSpeak/Sent; XDG Documents on Linux), re-created if deleted; saved folders still refuse when missing; a synced Documents (iCloud, Dropbox, Google Drive, OneDrive, any File Provider) is labelled and receipted as leaving the device
- #862 — First run review fixes: a late mic grant is stopped; the owner's aliases never claim a named other person; FOUND shows one true default; a blocked mic shows tokens, not a paragraph
- #861 — API manifest and census for the first-run FOUND control (main was red after #859)
- #859 — First run "C1 · Heard first" (ratified): one Set up local AI press; First words lights when speech lands; his first sentence played back big; his name and aliases count in needs-you; FOUND engines with Use it. Merged on the owner's word before Astra's review finished
- #856 — llama.cpp runtime in the base install; one-press Set up local AI (sha-pinned Whisper, embedding and starter models, one egress receipt); no download at boot or on load; the starter serves meeting analysis; meetings summarised by default when an engine exists
- #855 — Batteries-included default: a local engine on this machine becomes "Default for AI work" by itself (loopback only, no proxy, no redirects; made_by stored with the assignment); LAN and cloud engines are proposals; memory follows a local or owner-made default
- #853 — Heartbeat: every_sweep no longer notifies in quiet hours; quiet-hours tests use fixed clocks (they failed nightly 2–3 and across DST)
- #852 — Chat no longer replays withdrawn recall: saved grounding is re-read per turn; saved memory tool results replay as a re-read note; containers keep live members
- #850 — Memory slice 6, backend: Ask and chat ground pages, then observations, then recall; refitted before every pass; `memory.page` in the chat palettes except Plan, no palette larger than before
- #848 — Memory slice 5, backend: standing pages per project and desk (dark until `memory.page` is assigned); every sentence checked against its cited inputs; withdrawn inputs withheld at read; drafters read pages as context
- #846 — The Door week test seeds inside the local week with one pinned clock (it failed on Sunday evenings)
- #845 — Memory dates by tense (next such day for things to come, last for things done), spans keep their length, no title-named projects; observation tables refuse rowid rewrites (EXTRACTOR_VERSION 2)
- #843 — Memory slice 4: observations with evidence and history (dark until `memory.consolidate` is assigned); each text version is served only while its own evidence is live in scope
- #841 — Nine harder relation questions: keyword search answers none, the entity walk answers all; a strict expected-fail for the initial alias
- #839 — Memory slice 3: fact extraction, entities and the entity walk (dark until `memory.extract` is assigned); facts serve only while their source text is live; extraction yields to foreground calls on the same engine
- #837 — The calendar test seeds its event in the local week (it failed every Sunday evening west of UTC)
- #836 — Recipe chat searches memory through the thread turn, proven by a live test; the agent tool turn is recorded as retired code
- #834 — An edited dictation is remembered by its new words (memory and the Journal search); Replay's before-text is the edited text
- #832 — Memory slice 2: Brief items, dictation, steward runs and Room answers are remembered; keyword search over the memory index works with no engine; time ranges compare as instants
- #830 — Memory for every AI job: one policy row per capability; cadence, decision, PR review and rails drafts read memory; memory fits the job's token budget; no self-recall
- #829 — Memory reads a time phrase from the question ("last week", "in September", "since Monday")
- #827 — Muad'Dib and the Fedaykin run on Opus 5.5 (owner ruling 2026-10-04)
- #819 — Evidence moved to branch `archive/evidence-2026-10-04` (16,389 files, 2.3 GB; `pm/ARCHIVE.md`); the tree is 10,612 files, 172 MB
- #812, #814, #799–#811 — The long-standing red browser tests fixed (29 stale tests, the rig's late-step verdict)
- #798, #801–#805 — Regressions from the 2026-10-03 merges fixed (merged rows keep sources, lamp labels, windows clear the Dock)
- #797 — The default run is green after "every write announces"
- #795, #796 — Memory slice 1: meaning search fused with keyword search; local embedding model; privacy and egress fences
- #787 — The memory design
- #794 — Floor list: a row can be selected and Get Info opens; rename works
- #777, #768 — Prep, the meeting summary, the 1:1 brief and the update draft read memory
- #785, #771 — Every write announces itself; the Room, People and Intelligence views follow
- #788 — One needs-you rule on the hub; every face reads its number
- #790, #781, #792 — Every New verb opens its window at once; the Thought window keeps every key
- #775, #779, #772 — "Name an owner", Workbench Run with no engine, Context save
- #789, #793, #778 — Faces that contradicted themselves; the Agents roster; times in the owner's zone (and a schedule repair)
- #786, #770, #774 — Summaries, sends, updates, Prep, calendar and actions are findable; Decide decisions findable in their Project; the palette searches content
- #791, #782–#784 — The default test run made green
- #767 — The sent Brief carries no People data; a stale prepared Brief refuses to send
- #769 — Chat guardrail and compaction find their engine by route
- #766 — Every MCP tool runs on the hub (11 were broken); calls stay in order
- #776 — An owned item reads "To review", not "Unassigned"
- #773 — The 2026-10-03 inventory
- #772 — Context saves; a failed save reads as plain words
- #765, #764 — Astra is the reviewer; one final review round, at most 2 iterations
- #763 — Fast tests
- #763 — Fast tests: 5 min 40 s default run, scoped browser tests, nightly full
- #762 — Generated docs out of git; test maps cite text, not lines; no count checks
- #761 — The commit gate is removed (branch, PR, one review, merge)
- #755 — Phase 13 close, Astra's record (B0 done; 18/18)
- #747 — Phase 13 B2
- #748 — Phase 13 B4, windows
- #759 — Phase 13 title bar design
- #760 — Fedaykin are Fable 5.1 (docs)
- #758 — Phase 13 story 11 close
- #757 — Phase 13 B0 reds fixed
- #754 — Phase 13 C4
- #756 — Phase 13 H-C4 attendees fix
- #753 — Phase 13 close, Astra's record
