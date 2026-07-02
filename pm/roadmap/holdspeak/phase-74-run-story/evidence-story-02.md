# Evidence — HS-74-02 — Run frames: the theater's heartbeat (hub)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-74-run-story`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **`_run_frame`** (primitives.py): one honest frame per state through
  `ctx.broadcast` — `intel_status {state, scope: "run", capability:
  {kind, id, name}, error?}`. Runs ride the SAME vocabulary the theater
  and the Queue HUD already consume (`running` reveals, `ready`/`error`
  settle); `scope: "run"` lets meeting-scoped consumers ignore them.
  Headless contexts (`ctx.broadcast is None`) stay silent; a frame
  failure never breaks a run.
- **Coverage**: agent (running → ready | error); chain (ONE bracket
  around the whole pipeline — no per-step noise; error on any step's
  502); workflow (both the graph and prompt paths; error on the prompt
  502 AND the unhandled graph-node 502 — the failure-policy `skip`/
  `fallback` continuations correctly do NOT emit error).
- **No token frames, ever**: the engine call is synchronous; fabricating
  a stream would be the exact fakery the Phase-73 finding refused.
- **The /live intel panel ignores run frames** (dashboard-app.js: one
  scope guard) — it is the MEETING's status card. The theater and the
  Queue HUD consume run frames as-is (a run IS a job; it belongs in the
  ledger).

## Verification artifacts

- `tests/unit/test_run_frames.py` — **4 passed** against the REAL app
  with a capturing broadcast: running-then-ready order + the capability
  identity; the 502 error frame with the engine's message; the
  one-bracket-per-chain rule; the no-token-frames lock.
- Story-01 + primitives route slices still green (42 together).
- Web build green with the dashboard guard. Full suite at ship: **3080
  passed, 37 skipped, 0 failures** (3076 + the 4 new).

## Acceptance criteria — re-checked

- [x] running precedes the engine call; ready/error settle; the frames
      carry the capability identity.
- [x] scope-tagged so the meeting panel ignores them; theater/HUD play.
- [x] No frames in headless contexts; no fabricated tokens (locked by
      test).

## Deviations from plan

- The plan said "no frames when ctx.broadcast is None — headless stay
  silent" as a test; it is enforced structurally (`_run_frame` returns
  first) and exercised implicitly by every non-web test context.

## Follow-ups

- HS-74-03 closes the loop on the desk (theater plays + the artifact
  materializes).
