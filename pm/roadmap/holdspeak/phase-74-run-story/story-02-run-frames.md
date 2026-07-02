# HS-74-02 — Run frames: the theater's heartbeat (hub)

- **Status:** todo
- **Severity:** MED
- **Depends on:** —

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
