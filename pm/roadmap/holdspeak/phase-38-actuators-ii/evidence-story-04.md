# Evidence — HS-38-04: Live in-meeting proposals + broadcast

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

An actuator proposal is now surfaced **live** — broadcast as the pipeline produces it,
shown in a dashboard "Pending actions" panel, and approvable on the spot — without
weakening the gate (actuators off by default; nothing runs without approval; the broadcast
carries no egress-capable payload).

### Backend — emit `actuator_proposed` (read-only)

- **`holdspeak/plugins/persistence.py`** — `record_actuator_proposal` now **returns** the
  persisted `ActuatorProposalRecord` (was `None`), so callers can surface it.
- **`holdspeak/plugins/pipeline.py`** — `process_meeting_state` gains an optional
  `on_proposal: Callable[[record], None]`. When a `proposed` run is persisted, it calls
  `on_proposal(record)` — **best-effort**: a callback failure is recorded on
  `result.errors`, never raised (persistence is never aborted). Default (no callback) is the
  byte-identical Phase-37 path.
- **`holdspeak/meeting_session.py`** — wires `on_proposal=self._emit_actuator_proposal` into
  the finalization-time MIR pipeline. `_emit_actuator_proposal` builds a **read-only** slim
  view — `id` / `meeting_id` / `plugin_id` / `status` / `target` / `action` / `preview` /
  `reversible` / `created_at` (ISO string) — and emits it via the existing
  `_emit_broadcast("actuator_proposed", …)` seam. The machine `payload` (egress
  source-of-truth) and `result`/`error` are **never** put on the wire.
- **`holdspeak/web_runtime.py`** — *unchanged*: `_on_meeting_broadcast` already forwards any
  message type outside its dedicated-handler set to `server.broadcast(type, data)`, so
  `actuator_proposed` flows to live clients automatically.

Because no actuator is registered or chained by default, **nothing broadcasts** on the
default path — dispatch/routing stays byte-identical.

### Frontend — the "Pending actions" panel

- **`web/src/scripts/dashboard-app.js`** — `pendingProposals` state; an `actuator_proposed`
  message handler (`addProposal`, deduped by id — overlapping windows re-propose under one
  idempotency key); `decideLiveProposal(proposal, decision)` POSTing to the **Phase-37
  decision endpoint** (`/api/meetings/{meeting_id}/proposals/{id}/decision`) and updating the
  row in place (storing only `status`/`decided_by`, never the echoed payload); and the
  `proposalStatusLabel` / `proposalAccent` / `proposalIcon` helpers (mirroring history-app).
- **`web/src/pages/index.astro`** — a Signal `.panel` "Pending actions" rail panel
  (`x-show="pendingProposals.length"`): per proposal a lifecycle-accented card with the
  `action → target` title, a typed status chip, reversibility, the human preview line, and
  **Approve / Reject** + the guard line "Nothing runs without your approval." Scoped CSS
  using the page's Signal tokens; the bundle (`holdspeak/static/_built/`, gitignored) rebuilt
  with `cd web && npm run build`.

The live approve path is the **same** gated decision endpoint as the saved-meeting surface;
approving records a decision (+ audit) and performs **no** side effect — execution remains
the guarded executor's job.

## Verification

### Targeted — broadcast contract + pipeline wiring

```
$ uv run pytest -q tests/unit/test_live_proposals.py
6 passed in 0.45s
```

- **Read-only broadcast** — `_emit_actuator_proposal` emits exactly the slim dict (asserted
  field-for-field) and **excludes** `payload` / `result` / `error`; `created_at` is an ISO
  string; no observer → silent no-op.
- **Return value** — `record_actuator_proposal` returns the durably-persisted record.
- **Pipeline wiring** — `process_meeting_state(on_proposal=…)` calls the callback with each
  persisted `proposed` record (dispatch stubbed to isolate from routing); the default (no
  callback) still persists; an `on_proposal` that raises is recorded on `errors`, not raised
  (persistence not aborted).

### Build + full suite

```
$ cd web && npm run build       # bundle gitignored — source only committed
8 page(s) built
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2123 passed, 15 skipped in 59.46s        # +6 vs HS-38-03 (the new live-proposal tests)
$ uv run ruff check holdspeak/plugins/pipeline.py holdspeak/plugins/persistence.py holdspeak/meeting_session.py tests/unit/test_live_proposals.py
All checks passed!
```

## Notes

- **Where live actuators generate (the story's open question):** the default — surface
  proposals **as the existing dispatch produces them**, which today is the finalization-time
  MIR pipeline (meeting `stop()`). The dashboard websocket is still connected at stop, so the
  `actuator_proposed` panel appears then. A dedicated live-dispatch cadence (mid-meeting
  ticks) is a documented follow-up if finalization timing feels too late; it would reuse this
  same `on_proposal` → broadcast seam.
- **No new execution path** — the live panel reuses the HS-37-03 decision endpoint verbatim;
  this story adds a *surface*, not a new way to act. Manual check (rebuild + a live/simulated
  meeting): the panel appears on a proposal, approve/reject flips state, nothing executes
  without approval.
