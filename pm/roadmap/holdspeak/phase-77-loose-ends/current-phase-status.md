# Phase 77 — Loose Ends (the Phase-72 follow-ups)

**Status:** open — scaffolded 2026-07-02 (0/4).
**Owner call that opened it:** picked from the three offered next-phase
candidates ("P72 loose ends + small fixes") while owner testing is
unavailable.

## Why

Phase 72 filed three concrete follow-ups it could not absorb: the
schema-documented loss of `agent.manual_context`/`use_zone_context`
through hub sync (an iPad-authored persona loses its pinned context on
every round trip), the Queue HUD deriving its jobs from side signals
instead of a real `runtime_queue` frame, and the coders-status payload
still reporting desk connector config (a residual conflation). All three
are hub-side and fully provable headless.

## Stories

| ID | Story | Sev | Status | Depends |
|---|---|---|---|---|
| HS-77-01 | The agent's pinned context survives the hub | HIGH | todo | — |
| HS-77-02 | A real `runtime_queue` frame for the Queue HUD | MED | todo | — |
| HS-77-03 | The coders-status conflation dies | MED | todo | — |
| HS-77-04 | Docs + closeout | MED | todo | 01–03 |

## Exit criteria

- [ ] `manual_context`/`use_zone_context` persist on the hub (schema v7,
      the guarded-ALTER precedent), ride the agent wire both ways, and a
      pushed iPad agent pulls back byte-faithful; the Swift tolerant-decode
      comment updated to say the loss ended (HS-77-01).
- [ ] The hub broadcasts a real `runtime_queue` frame on queue
      transitions and the Queue HUD consumes it as its primary source
      (HS-77-02).
- [ ] `/api/coders/status` reports coder sessions only; the desk
      connector config leaves the payload (its consumers verified first)
      (HS-77-03).
- [ ] Entry-point docs touched where they speak; guards + full suite
      green; PR merged on a conclusion-checked green (HS-77-04).

## Where we are

**2026-07-02 — scaffolded (0/4).** All three targets verified in code
before scaffolding (the agents DDL, the Swift tolerant-decode comment
documenting the loss, the P72 final-summary follow-up list).
