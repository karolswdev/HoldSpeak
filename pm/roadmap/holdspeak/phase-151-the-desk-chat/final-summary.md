# Phase 151 — The Desk Chat: The Thread (DC-01) — final summary

**Closed 2026-08-30 (8/8) in one sitting from the plan's filing.** The
branch holds for the owner's shot verdict and merge word (PR #507, which
also carries the RFC and backlog AF).

## The one sentence, delivered

A Thread is a desk object: opened from anything on the desk (or from
nothing), spoken or typed into with `@`-refs frozen at the moment of
asking, streamed token by token over the one bus, badged and receipted
per turn, stoppable, branchable, keepable — and found again by search,
because every byte lives in the hub's SQLite, never in a browser.

## What shipped (by story)

| Story | Delivered | Proof |
| --- | --- | --- |
| 01 The thread ledger | `threads` / `thread_messages` (parent_id tree, `streaming`, kernel provenance) / `thread_message_parts` (`sensitive`) / `thread_refs` / FTS with soft-delete-aware triggers; `ThreadRepository`; import dedup | 32 passed; snapshot diff = exactly the block |
| 02 The capability | `chat.turn` sealed; `recipe.chat` retired; assignment chain carried by an idempotent backfill; the three 143 ledgers regenerated | 70 passed |
| 03 The streaming seam | `InferenceRunner.invoke_stream` in the same envelope; typed `Delta`s from `engine._chat_completion_deltas`; `StreamingPromptAdapter`; `StreamCadence`; three `thread_*` frames | 34 passed |
| 04 The turn route | `ThreadService` + `/api/threads`; `RoutedInferenceCoordinator.execute_stream`; frame per delta with seq; abort → indeterminate; branch/regenerate; the assembler law | 85 → 93 passed |
| 05 The Thread on the Desk | `thread` PrimitiveKind; `threads.ts`; `ThreadPullout` (streaming rows, RAW fold, error/CRASHED rows, `‹ n/m ›`, receipt short-id); registry verbs + 148 menus | baseline check 5/5 inherited |
| 06 The composer | mic arms never sends; Enter/Shift+Enter/Esc; Send↔Stop; `@` over kind-tagged primitives; `/` on the registry; inline branch/fork | 49 vitest; e2e 3/3 |
| 07 Search, list, retirement | `thread` memory corpus; Threads rows on Person/Meeting; one-time import; `chat.ts` + `PersonaChat` deleted | 56 pytest |
| 08 The walk and the close | rig, e2e, metal script, door-walk leg, docs, web baseline, close counsel, M5 | below |

## The proof (Art. IX)

- **Real metal `.43` (llama.cpp Q6, Qwen3.6-35B):** two streamed turns,
  bus-measured first delta **0.98 s / 0.93 s** (first run) and
  **0.90 s / 1.37 s** (final server) — N1 ≤ 1.5 s; 60–208 deltas per
  turn; receipts and `local` egress on every turn; control Ask 1.3–4.7 s
  non-streaming.
- **People boundary under profile switch (M1/M5):** the CAPTURED cloud
  request body contains no sentinel and carries `[people content
  withheld]`; local keeps it verbatim; verbatim again after switching
  back. Pinned through the real coordinator both ways.
- **Glass (rig, 1440 + 393):** empty, mid-stream (cursor), done (receipt
  short-id + lamp), branched (`‹ 2/2 ›`), error (severity + reason),
  CRASHED + Retry; the foot inside the card (asserted); no horizontal
  overflow at 393. `assets/story-08-shots/`.
- **e2e:** progressive deltas, receipt on done, Stop→Send after abort.
- **Door walk:** 10/10 legs including the new `thread` leg (Continue in
  thread from a Door object → pullout with the ref chip → turn).
- **Close sweep:** 6988 passed; 14 branch-new reds all dispositioned
  (fixed / rewritten / deleted with reason) — see evidence-story-08.
- **Web baseline:** the handover §3.D rider — built here as
  `scripts/web_baseline_check.py`, then FOLDED at merge into the sibling
  Phase 150 (Delegation + Monday) instrument that landed first:
  `scripts/check_web_baseline.py` + `tests/web-inherited-baseline.txt`
  (its `chat.test.ts` line removed: this phase deleted that test).
- **AGPL:** `git grep -i warpdrv` hits only the plan and this record.

## What the proof caught (the arc's scar list)

1. Real-Chromium: a hard crash on `?open=thread:<id>` and four
   client/server wire mismatches that jsdom passed.
2. The route built `ThreadService` with `broker=None` — every HTTP turn
   would have 500'd.
3. The streaming runner's published result lacked `provider`/`model` and
   leaked `usage`; the sealed schema rejected it and every turn failed
   silently (no error persisted).
4. Abort found no cancel event — per-request service instances.
5. Counsel M5: the M1 redactor existed and was pinned but the turn
   pipeline never called it. Now applied at the coordinator's payload
   reconstruction, where the frozen route plan is finally known.
6. `@person` refs refused the whole turn (no `person` kind in grounding)
   and the composer's ref objects didn't match the service's strings.
7. `SurfaceFooter` is a fixed 36 px bar — the composer overflowed the
   window.
8. The thread walk leg passed hollowly when it couldn't find its subject.

Every one of these lived only in the seams between builders' fakes and
the real path. The standing law this arc adds: **drive the real
coordinator with a fake engine factory; a fake adoption service proves
nothing about admission, receipts or egress.**

## Counsel

Design beat: RATIFY-WITH-CONCERNS (M1–M4, all built). Close:
RATIFY-WITH-CONCERNS — M5 fixed in-round; S5 (process-level cancel
registry), S6 (thread FTS rebuild path), S7 (error taxonomy) ride
DC-02; R6–R8 recorded. Beauty list taken in full (tokens only, quiet
provenance line, secondary verb toolbar, primary Retry, 393 composer).

## Held for the owner

- The shot exhibit (both widths) before merge; the merge word.
- RFC §14 defaults taken this arc (window not wing; effect tools yolo
  in DC-02; Kokoro server-side in DC-04; no external MCP) — overrule at
  the sitting.
- DC-02 The Hands is the natural next leg: the tool loop on the kernel's
  tool turns over the in-process MCP families — the point at which the
  Thread becomes a manager's hands, not only a voice.
