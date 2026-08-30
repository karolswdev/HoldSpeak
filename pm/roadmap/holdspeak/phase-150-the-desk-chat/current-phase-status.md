# Phase 150 — The Desk Chat: The Thread (DC-01)

**Status:** building (5/8). Design-beat counsel RATIFY-WITH-CONCERNS;
M1–M4 accepted into the settled design. Building.

**Last updated:** 2026-08-29.

## Owner mandate

The owner asked for a realistic port of the warpdrv chat experience
(`docs/internal/PLAN_PHASE_DESK_CHAT.md`, backlog AF) and then said,
verbatim: **"Let's impl it!"** This phase is DC-01 of that plan — the
keystone every later DC phase stands on. Branch
`worktree-warpdrv-chat-port` from main `c9b0cd25` (PR #507 carries
the plan and this phase).

Standing laws with extra weight: **no AGPL-derived source** (the
warpdrv clone never enters the repo; workers get the settled design,
not the clone); the value frame (a chat OVER the desk, not a chat
app); Art. I/II (Thread = desk object, no chat screen); Art. III
(one egress badge per turn); Art. IV (voice arms, never fires);
Art. V/XI (every turn admitted + receipted, one admission path);
Art. IX (real metal on `.43` before any flip); the People hard
boundary at MESSAGE level (counsel M1); shots before merge.

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — every seam
  file:line. Headlines: the runner is SYNC and has no stream variant;
  `engine._chat_completion_stream` EXISTS (L337) and is the seam;
  frames are a hand-mirrored sorted tuple with a drift test; no
  upload route / no PDF extraction (attachments out of DC-01);
  `recipe.chat` is a live sealed capability to retire.
- [`assets/counsel-design-beat.md`](./assets/counsel-design-beat.md)
  — RATIFY-WITH-CONCERNS; M1 people-part redaction at assembly, M2
  cadence + `streaming` flag, M3 FTS soft-delete triggers, M4
  `turn_started` committed before the first delta; S1–S4 accepted;
  R1–R5 recorded; story 02/03 reordered.
- [`assets/settled-design.md`](./assets/settled-design.md) — D1–D8.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-150-01 | The thread ledger (schema + repository + import) | done | [story-01](./story-01-thread-ledger.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-150-02 | The capability (chat.turn sealed + assigned) | done | [story-02](./story-02-capability.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-150-03 | The streaming seam (invoke_stream + typed deltas + frames) | done | [story-03](./story-03-streaming-seam.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-150-04 | The turn route (threads API, refs frozen, abort, branch, keep) | done | [story-04](./story-04-turn-route.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-150-05 | The Thread on the Desk (primitive, verbs, ThreadPullout, streaming renderer) | done | [story-05](./story-05-thread-pullout.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-150-06 | The composer (mic, @-refs, send/stop, / verbs) | in-progress | [story-06](./story-06-composer.md) | - |
| HS-150-07 | Search, list and retirement (FTS corpus, list view, Threads rows, chat.ts import + delete) | in-progress | [story-07](./story-07-search-list-retire.md) | - |
| HS-150-08 | The walk and the close (real metal, glass, docs, counsel) | in-progress | [story-08](./story-08-walk-and-close.md) | - |

## Where we are

**5/8 — THE THREAD IS ON THE DESK.** HS-150-05 is DONE — `thread` is a PrimitiveKind through both type gates and the list band; `threads.ts` (client + zustand slice + bus subscription by seq) and `ThreadPullout` (head lamp/status/meter, streaming rows via `StreamingMaterial`, reasoning behind RAW, error row in-flow, CRASHED+Retry, `‹ n/m ›`, receipt short-id) with `New thread` / `Continue in thread` on the registry and the 148 object menus. Glass caught what jsdom could not: a hard crash on `?open=thread:<id>` and four wire-contract mismatches; all fixed in-round, rig failures=0. Web baseline check: 5/5 inherited, zero new reds. Earlier — **4/8 — THE SERVER STREAMS.** HS-150-04 (the turn route) is DONE — ThreadService + `/api/threads` (create/list/get/patch/delete/turns/abort/branch/regenerate/keep/import); the turn admits `chat.turn` through the adoption service with Ask's exact envelope, COMMITS the assistant row and broadcasts `thread_turn_started` before the provider stream opens (M4), then a daemon thread drives the new `RoutedInferenceCoordinator.execute_stream` (same bookkeeping as `execute`, `invoke_stream` underneath) — frame per delta with a monotonic seq, DB flush per StreamCadence (M2); abort → indeterminate + done{aborted}; branch/regenerate = siblings; the ASSEMBLER LAW pinned both ways (M1: sensitive parts → `[people content withheld]` on a cloud route, verbatim on local); unknown ref refuses by name before any row; `/api/recipes/{id}/chat` is the thread alias; the 7 retired RecipeService.chat tests DELETED (they tested retired behaviour). First pass stopped short (non-streaming execute, one part) — caught by orchestrator read and closed in-round. 85 passed orchestrator-read; the 2 placement reds are baseline names 33–34 of the 143 file. Earlier — **3/8.** HS-150-02 (the capability) is DONE — `chat.turn` sealed, `recipe.chat` RETIRED (route → 410 named stub until 04's alias; MCP dispatch → retired error, tool count unchanged; `_SUBJECT_CAPABLE` + the lease kind re-pointed), backfill family `chat-route-assignments` (copy recipe.chat → else ask.answer → chat.turn, idempotent, never overwrites), the three 143 ledgers + one_path fences regenerated to absorb 03's line shifts (`_attempt_stream` pinned as a second context-mint scope — an honest widening of the Phase-131 fence, recorded here); 70 passed orchestrator-read; 7 old RecipeService.chat tests skipped BY NAME with the story id. Left for 04: `RecipeService.chat` body + the alias; for 05: PersonaChat.tsx + the 143 assignments glass label. Earlier — **2/8.** HS-150-03 (the streaming seam) is DONE — `InferenceRunner.invoke_stream` beside `invoke` in the same admission/plan/receipt envelope (fallback only before the first delta; `indeterminate` on cancel or late error), `ProviderAdapter.dispatch_stream` with a default that wraps `dispatch` so every existing adapter keeps working, typed `Delta`s from `engine._chat_completion_deltas` (content / reasoning_content / usage for both the OpenAI and llama.cpp shapes, absence tolerated), `StreamingPromptAdapter` for story 04, `StreamCadence` (500 chars / 2 s / done — counsel M2), the three `thread_*` frames mirrored with the drift test green; 34 passed orchestrator-read; one_path spine/cardinality reds (10) verified pre-existing by the builder against clean code — carried to the close sweep. Landed ahead of 02 as a commit (02's census fixtures absorb 03's line shifts). Earlier — **1/8.** HS-150-01 (the ledger) is DONE — threads / thread_messages (parent_id tree, `streaming`, kernel provenance) / thread_message_parts (`sensitive`) / thread_refs / thread_messages_fts with soft-delete-aware triggers; ThreadRepository with the full D1 surface + D7's import dedup (`import_hash` ref row); snapshot fixture regenerated (diff = exactly the block); 25 new tests + snapshot + reconcile-twice green (32 passed, orchestrator-read). Builder decisions recorded in evidence: REAL epoch timestamps (newer-table convention), FTS on implicit rowid, nullable `thread_refs.message_id` for thread-level refs. 02 and 03 build in parallel. Earlier — **Chartered — 0/8.** Census + counsel done in one sitting after the
plan was filed; the settled design carries all four must-fixes. Wave
1 = 01 (ledger); wave 2 = 02 → 03 → 04 (serial: capability, stream,
route); wave 3 = 05 → 06 ∥ 07; close = 08.

## Exit criteria (evidence required)

- [ ] F1–F7, N1–N5 of the RFC proven with evidence files.
- [ ] Counsel's three walk legs recorded (real metal `.43`, People
      boundary under profile switch, glass exhibit both widths).
- [ ] `chat.ts` deleted after a one-time import; `recipe.chat` retired.
- [ ] Close counsel zero must-fix; owner shot verdict before merge.
- [ ] `git grep -i warpdrv` hits only the plan and this phase's records.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Streaming inside frozen plans breaks fallback semantics | medium | D3: fallback only before first delta; after = indeterminate + Retry | a receipt lies about which model produced visible text |
| People content leaks through message history to cloud | low | D4 assembler law + M1 pin test + walk leg 2 | any sensitive text in a recorded cloud payload |
| SQLite write contention from delta persistence on `.43` | medium | D3 cadence (2 s / 500 chars) | bus stalls > 1 s during a turn |
| AGPL taint by an over-helpful worker | low | clone deleted; N5; close grep | any file citing a warpdrv path |
| Web-unit baseline blind spot hides a real regression | medium | story 08 lands the baseline file + check | a new red name not in the six |

## Decisions made (this phase)

- 2026-08-29 — RFC §14 defaults: Desk window (not wing); effect tools
  yolo (DC-02); Kokoro server-side (DC-04); no external MCP —
  orchestrator, owner may overrule.
- 2026-08-29 — `recipe.chat` retired into `chat.turn` (counsel S1).
- 2026-08-29 — attachments = `@`-ref chips only; file upload deferred
  (no upload route exists; census §9).
- 2026-08-29 — no SSE endpoint; the one WebSocket bus carries deltas.

## Decisions deferred

- Vector search over threads (RFC §4.2) — trigger: FTS recall proven
  insufficient on the owner's real data.
- File attachments + PDF extraction — DC-02 rider.
