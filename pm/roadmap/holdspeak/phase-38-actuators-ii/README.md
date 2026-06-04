# Phase 38 — Actuators II

**Status:** not-started — **scaffolded 2026-06-04**. The live plan is
[current-phase-status.md](./current-phase-status.md) (goal, scope, exit criteria, the
6-story table, risks, decisions). This README is the framing note; the status doc is
canon if they disagree.

Phase 37 proved actuators are **safe** (propose → approve → execute → audit, gated). It
shipped **dormant** — one reference actuator writing a local file, approval only on the
saved-meeting detail. Phase 38 makes the mechanism **useful** without weakening a single
guarantee: **real write connectors** behind a per-connector permission manifest, and
**live in-meeting proposals**.

## The plan (scaffolded)

Six stories. The Phase-37 invariant is load-bearing throughout — *no external side effect
without an explicit, audited, per-action human approval; executed == previewed* — and
every new connector adds a *narrower* gate (its permission manifest), never a looser one.

1. **HS-38-01** — gated write-connector framework + per-connector **permission manifest**
   (the safety seam; routes every outbound call through `PermissionGate`).
2. **HS-38-02** — GitHub write connector (`gh issue create`, `shell:exec`).
3. **HS-38-03** — webhook write connector (HTTP POST to an allow-listed host,
   `network:outbound`; covers Slack/Teams incoming webhooks).
4. **HS-38-04** — live in-meeting proposals (broadcast + a live approve/reject panel).
5. **HS-38-05** — Actuators II documentation (write connectors + live proposals).
6. **HS-38-06** — closeout + final-summary.

Grounded in the existing seams: the Phase-37 `ActuatorExecutor` takes any injected
`connector(proposal) -> dict`; `connector_runtime.PermissionGate` already gates
`run_subprocess` (`shell:exec`) + `open_outbound_socket` (`network:outbound`);
`connector_sdk.ConnectorManifest` already carries `permissions`/`requires_network`; and the
live event path is `WebRuntime` `server.broadcast(type, data)`. See
[current-phase-status.md](./current-phase-status.md). HS-38-01 is the entry point.
