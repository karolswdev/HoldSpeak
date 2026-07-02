# Evidence — HS-77-02 — A real `runtime_queue` frame for the Queue HUD

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-77-loose-ends`)

## What changed

- **`build_runtime_queue_frame(db)`** (intel_queue.py): the deferred-intel
  queue's REAL truth — up to 20 listable jobs (`intelq:<meeting_id>`,
  meeting-title labels, status, attempts) + the aggregate summary
  (queued/running/failed/scheduled retries/next retry).
- **Broadcast on transitions**: the `/api/intel/process` route after a
  drain; the runtime's deferred loop after processing a job; the
  process-plugin-jobs path after the flush. Frame failures never break a
  job.
- **The HUD consumes it as the primary source** (`fromRuntimeQueue`):
  real rows reconcile in (upsert by frame id; the note shows real attempt
  counts), and a row that LEAVES the frame resolves through the HUD's own
  linger grammar (done → the 4s prune) rather than vanishing — the first
  implementation deleted instantly and the proof run caught it fighting
  the ledger's design. The header comment ("the web has no runtime_queue
  feed") is rewritten; live non-queue activity stays derived, as
  documented.

## Verification artifacts

- `tests/unit/test_runtime_queue_frame.py` — **3 passed**: the frame's
  jobs + summary from a seeded queue; the honest empty frame; the route
  broadcasting exactly one frame after a (stubbed) drain against the real
  app.
- **Playwright**: a real broadcast revealed the HUD with all three rows
  (labels + "attempt 3"); the emptied frame showed the resolution linger
  and then pruned (`02-hud-real-queue.png`). Zero page errors.
- Full suite at ship: **3095 passed, 37 skipped, 0 failures** (3092 +
  the 3 new).

## Acceptance criteria — re-checked

- [x] The hub broadcasts real queue truth on transitions; the HUD renders
      it as the primary source, honoring its own linger grammar.
