# HS-74-02 — Run frames: the theater's heartbeat (hub)

- **Status:** done
- **Severity:** MED
- **Depends on:** —
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## What

The run routes broadcast honest `intel_status` frames through
`ctx.broadcast` so the shell GenerationTheater plays for persona runs the
same way it plays for meeting intel. No fake tokens: the engine call is
synchronous, so the frames are `{state: "running"}` before and
`{state: "ready"}` after (`{state: "error"}` on failure) — exactly the
states the theater already consumes.

## Test plan

- Route test with a capturing `ctx.broadcast`: running precedes the
  engine call, ready follows success, error follows a 502; no frames when
  `ctx.broadcast` is None (headless contexts stay silent).

## Done

Shipped. One `_run_frame` helper broadcasts honest `intel_status` frames
(running → ready | error) tagged `scope: "run"` with the capability
identity — the same vocabulary the theater and Queue HUD already consume,
while the meeting-scoped /live panel gains a one-line scope guard. Chains
bracket ONE frame pair around the whole pipeline; workflows cover both
paths including the unhandled graph-node 502 (failure-policy
continuations correctly emit nothing); headless contexts stay silent; and
the no-fabricated-tokens rule is a lock, not a promise. 4/4 against the
real app with a capturing broadcast. See
[evidence-story-02.md](./evidence-story-02.md).
