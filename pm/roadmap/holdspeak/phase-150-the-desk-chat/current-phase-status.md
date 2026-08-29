# Phase 150 — The Desk Chat: The Thread (DC-01)

**Status:** building (1/8). Design-beat counsel RATIFY-WITH-CONCERNS;
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
| HS-150-02 | The capability (chat.turn sealed + assigned) | in-progress | [story-02](./story-02-capability.md) | - |
| HS-150-03 | The streaming seam (invoke_stream + typed deltas + frames) | in-progress | [story-03](./story-03-streaming-seam.md) | - |
| HS-150-04 | The turn route (threads API, refs frozen, abort, branch, keep) | backlog | [story-04](./story-04-turn-route.md) | - |
| HS-150-05 | The Thread on the Desk (primitive, verbs, ThreadPullout, streaming renderer) | backlog | [story-05](./story-05-thread-pullout.md) | - |
| HS-150-06 | The composer (mic, @-refs, send/stop, / verbs) | backlog | [story-06](./story-06-composer.md) | - |
| HS-150-07 | Search, list and retirement (FTS corpus, list view, Threads rows, chat.ts import + delete) | backlog | [story-07](./story-07-search-list-retire.md) | - |
| HS-150-08 | The walk and the close (real metal, glass, docs, counsel) | backlog | [story-08](./story-08-walk-and-close.md) | - |

## Where we are

**1/8.** HS-150-01 (the ledger) is DONE — threads / thread_messages (parent_id tree, `streaming`, kernel provenance) / thread_message_parts (`sensitive`) / thread_refs / thread_messages_fts with soft-delete-aware triggers; ThreadRepository with the full D1 surface + D7's import dedup (`import_hash` ref row); snapshot fixture regenerated (diff = exactly the block); 25 new tests + snapshot + reconcile-twice green (32 passed, orchestrator-read). Builder decisions recorded in evidence: REAL epoch timestamps (newer-table convention), FTS on implicit rowid, nullable `thread_refs.message_id` for thread-level refs. 02 and 03 build in parallel. Earlier — **Chartered — 0/8.** Census + counsel done in one sitting after the
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
