# Phase 37 — Actuators

**Status:** in-progress (4/7) — opened 2026-06-04. The live plan is
[current-phase-status.md](./current-phase-status.md) (goal, scope, exit criteria, the
6-story table, risks, decisions). This README is the framing note; the status doc is
canon if they disagree.

The plugin system's third kind. Today the host's `actuator` kind is **blocked**
(`plugin_sdk.validate_manifest` rejects it as deferred). Phase 35 built the
groundwork — the public authoring guide, the pack manifest + discovery loader, and the
capability model. This phase turns actuators on: a plugin that, instead of producing a
read-only artifact, proposes an **external side effect** (file a ticket, post a
message, open a PR, …) behind a **preview → human approval → execute** flow.

This is the RFC's open question #5 and it **intersects the Phase-25 egress posture**
(no silent cloud egress; approval + audit before any outbound action), so it is its own
phase rather than a tail of Phase 35.

## The plan (scaffolded)

Seven linear stories — each consumes the prior, because the safety invariant ("no external
side effect without an explicit, audited, per-action human approval; executed ==
previewed") is only meaningful end-to-end:

1. **HS-37-01** — actuator contract (`ActuatorProposal`) + unblock the kind, proposal-only,
   gated.
2. **HS-37-02** — proposal persistence + lifecycle (`proposed → approved → executed |
   rejected | failed`) + audit.
3. **HS-37-03** — approval surface (preview → approve/reject; no execution on view).
4. **HS-37-04** — guarded executor + audit + governance gate (payload parity, policy,
   Phase-25-gated egress).
5. **HS-37-05** — one reference actuator end-to-end (incl. "no approval ⇒ no action").
6. **HS-37-06** — actuator documentation (project docs update; after 05 so the authoring
   guide shows a real example).
7. **HS-37-07** — closeout + final-summary.

Grounded in `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` (open question #5) + the
Phase-25 egress posture. The seam already exists: `plugin_sdk.validate_manifest` rejects
the `actuator` kind, and `PluginHost(allow_actuators=False)` blocks it — HS-37-01 unblocks
*proposing*, HS-37-04 gates *executing*. See [current-phase-status.md](./current-phase-status.md).
