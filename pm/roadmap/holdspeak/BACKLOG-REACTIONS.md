# Reactions backlog

## Implemented v1 seam

- Connector **Watches** accept typed GitHub PR or Jira issue snapshots.
- The first successful snapshot is a quiet baseline.
- Later snapshots publish durable, deterministic events into the shared typed
  service-event ledger. The same ledger accepts events from every service.
- Enabled **Reactions** idempotently project matching events into one configured
  Workbench.
- MCP invokes the existing service layer; v1 mutation and execution require the
  authenticated `OWNER` principal.
- GitHub Watches can query normalized pull-request snapshots through the
  read-only, allowlisted `gh` connector adapter.
- The local conductor refreshes enabled Watches every 35 minutes by default,
  with a per-Watch cadence override. Refresh failures are isolated and retain
  the last good baseline; the same heartbeat projects intrinsic ledger events.
- The Workbench configuration surface owns a batteries-included GitHub review
  preset: repository scope, non-mutating test, silent baseline, pause/enable,
  health, and delivery history. Connector credentials remain in Settings.
- Intrinsic **Resourceful when idle** policies require no connector. The local
  conductor records one durable idle epoch, discovers a typed opportunity, and
  admits exactly one causal Workbench item. Default policy: 30 minutes idle,
  six-hour cooldown, overnight 22:00–07:00, target two admitted routines per
  night.
- The initial deterministic opportunity providers are Notes filed in the
  `Loose Ideas` Directory and failed Workbench items needing recovery plans.
  Candidate source revisions are durable, so restart/retry never presents an
  unchanged opportunity as new work.
- Workbench execution now supports an explicit item scope. Resourceful work and
  Reaction auto-run cannot sweep unrelated pending items.

Connector packs should query their own source and submit normalized snapshots.
They must not make each Reaction poll independently, and Reactions must not mine
arbitrary presentation text. A failed refresh retains the last good baseline and
records the error; missing entities are not interpreted as deletion.

`pipeline_events` remains operational call telemetry. Typed service events are
explicit domain facts. The service has an OWNER-only auto-run seam with exact
causal item scope, but v1 does not expose it in the product UI. Product delivery
therefore stops after adding one grounded item.

## Explicitly deferred

**Principal-aware Reaction execution:** replace OWNER execution with a restricted
SERVICE/AGENT principal and per-capability authority. This includes delegation,
revocation, scoped reads, and effect authority. It is not required for v1.

Also deferred: webhook ingress, the Jira query adapter,
delivery retry controls, identity-stable GitHub reviewer predicates, active
provider cancellation when ordinary work arrives mid-inference, additional
intrinsic opportunity providers, and richer temporal signals such as Jira
`due_soon`.
