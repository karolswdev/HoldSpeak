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

Now: prepare for the owner's week of real use (assignment 2026-10-03): inventory
(`docs/internal/INVENTORY-2026-10-03.md`), clean up, polish, wire memory into every
process; and the native memory system (`docs/internal/MEMORY-DESIGN.md`, slice 1 merged).

Test state on main `f1dc2c577` (2026-10-04, quiet machine): default run 13,407 passed,
0 failed (6 min 18 s); web 3,352 passed, 1 flaky; browser tests 747 passed, 1 failed
(the Decide button, #813). After a batch of merges, run all three before calling it done.

| Item | Owner | PR |
|---|---|---|
| Decide is outlined while "Run summary" shows; one flaky web test | Muad'Dib | #813 + one |
| Memory: turn meaning search on from the product (the embedding model is not in the signed catalogue): waits for the owner's word | — | — |
| Memory facts: the model writes PAST dates for a day with no month ("the ninth" on 22 Sep became 9 Sep; also "September 20" from a 23 Sep source) — the extraction prompt needs the next-such-day rule | Muad'Dib | after slice 4 |
| Memory entities: an initial alias ("T. Wierzbicki") does not join the full name (score 0.585 < 0.6 without a shared neighbour); strict xfail in the bench | — | — |
| Memory slices 4–6: observations; standing pages (needs a canvas); palette and Ask | Muad'Dib | — |
| Memory facts: off until `memory.extract` is assigned; never run through the product path with the real LAN model; entity kind as a list raises TypeError with no back-off job; the conductor reports calls 0 after a provider exception; a crashed open call holds extraction up to 600 s | — | — |
| Memory: summary and topic as their own chunks not built (needs old vectors to serve during a re-cut); thread keyword search misses bare local time ranges (inherited); the Desk memory face does not show the four new kinds | — | — |
| Memory: the agent tool turn (RecipeService.chat → run_recipe) is retired code with no caller; Recipe chat runs as a thread turn whose default tools include memory.search (proved by tests/unit/test_thread_memory_search_live.py). The update draft and Prep are not fitted to a token budget (their path has none) | — | — |
| Memory: live meeting analysis and voice resolve read no memory (a lookup is 100–400 ms against a 50 ms bar) | — | — |
| Memory: the decision-promotion self-recall test passes before the fix; mint through DecisionLifecycleService.promote (Astra, #830) | — | — |
| A PR review after its linked story is edited (same commit and diff) returns HTTP 500, as on main | — | — |
| Memory: a secret said in a meeting or typed in a thread is still a search key (returned text is redacted); sources attached by hand are not redacted | — | — |
| Memory: not measured on the owner's real desk; new items take up to 120 s to become searchable by meaning | — | — |
| Bus: background writers (calendar ingest, heartbeat sweep, cadence tick) and MCP tools outside the registry send no frame; announcements carry an empty id and op "create" on some routes | — | — |
| Needs you: a decision waiting for review is not a member; "waiting on someone" rows count in the number: waits for the owner's word | — | — |
| Needs you: the shade and palette show a per-Room count; the Chair caption "BRIEF · N THINGS WAITING" is a different count | — | — |
| Times: about 150 writers still store timestamps with no zone; a schedule edited under the old code keeps a wrong time until saved again | — | — |
| MCP: three tools answer a bad id with a raw error; a long tool makes the others wait | — | — |
| Sent Brief: People text stays in old prepared and discarded rows on disk; the re-render check covers the Brief only | — | — |
| Product word list lacks decision, workbench and thread (Get Info falls back; other callers can still throw) | — | — |
| The roadmaps read takes 2–3 s on each desk refresh | — | — |
| The Thought window title always says "Thought"; 1:1 memory has no face; route chip for Ask and chat: each needs a canvas | — | — |
| The Dock overflows 1440 with five projects; a 5 px strip of the next page shows at 393 | — | — |
| Raw paths and ids on some faces (SEND well, Connections, Setup, Processes) | — | — |
| Four June PLAN docs in the Source canon list name dead modules: waits for the owner's word | — | — |
| Backend: 219 routes with no web caller; two watch systems; three decision surfaces; 2,800 lines with no importer | — | — |
| Test rig: the Delivery board may show the machine's real tmux sessions | — | — |
| Fast tests, second pass: new-database cost; nightly full run not yet seen on CI | — | — |
| C1-4e: the Chair reopens 12 px low | — | — |
| The Roadmap window shows the wrong name; Calendar shows technical refusal text; the palette shows noise rows for "send" | — | — |

## Last merged (newest first)

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
