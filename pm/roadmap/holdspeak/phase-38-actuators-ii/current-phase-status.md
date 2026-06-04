# Phase 38 — Actuators II

**Status:** in-progress (3/6 stories — HS-38-01, HS-38-02, HS-38-03 done). Scaffolded
2026-06-04, immediately after Phase 37 — Actuators closed + merged via PR #14.

**Last updated:** 2026-06-04 (**HS-38-03 done** — the webhook write connector, the
`network:outbound` reference. `holdspeak/plugins/builtin/webhook_post_actuator.py`:
`WebhookPostActuator` proposes an HTTP POST `{url, body}` (url from `context["webhook_url"]`),
and `build_webhook_connector(allowed_hosts=…, client=…)` POSTs **only to an allow-listed
host** via `build_gated_connector` (`network:outbound` through
`PermissionGate.open_outbound_socket`); an off-list host is refused before egress (client
never invoked), a non-2xx / transport error → `failed` + audit, the status is returned. The
host allow-list is the **resolved HS-38-01 deferral**: `MeetingConfig.webhook_allowed_hosts`
(default-empty ⇒ nothing posts). Both gate kinds are now proven on the framework
(`shell:exec` + `network:outbound`). 13 new tests (full loop with an injected client — no
real HTTP); full suite **2117 passed, 15 skipped**; ruff + F821 clean. ◀ next: HS-38-04 live
in-meeting proposals.)

**Earlier 2026-06-04** (**HS-38-02 done** — the GitHub write connector, the first real
write on the HS-38-01 framework. `holdspeak/plugins/builtin/github_issue_actuator.py`:
`GithubIssueActuator` proposes a GitHub issue for the first unowned action item (payload
`repo`/`title`/`body`), and `build_github_issue_connector(runner=…)` runs **`gh issue create`
and only that** via `build_gated_connector` (`shell:exec` through `PermissionGate`,
manifest-allow-listed); argv is built from the stored payload (no shell → no injection), a
non-zero `gh` exit raises → `failed` + audit, the created issue URL is returned. Host-side
gated connector (executor injects it), not a discovered pack; opt-in + off by default. 12
new tests (full loop with an injected runner — no real `gh`); full suite **2104 passed, 15
skipped**; ruff + F821 clean. ◀ next: HS-38-03 webhook connector.)

**Earlier 2026-06-04** (**HS-38-01 done** — the gated write-connector framework +
permission manifest. `holdspeak/plugins/gated_connector.py`: `WriteConnectorManifest`
declares one egress permission (`shell:exec`/`network:outbound`) + a concrete allow-list
(argv prefixes / hosts); `build_gated_connector(plan, interpret, …)` enforces
**plan → allow-check → gate → interpret** per proposal — a refused op raises
`ConnectorOperationRefused` *before* any egress, an admitted op routes through the existing
`PermissionGate`. The `ActuatorExecutor` is unchanged; nothing is registered, so routing
stays byte-identical and the default suite makes no real outbound call. 12 new tests; full
suite **2092 passed, 15 skipped**; ruff + F821 clean. ◀ next: HS-38-02 GitHub connector.)

**Earlier 2026-06-04** (phase **scaffolded** — plan + 6 stories. Direction chosen by
the user: build on the proven-safe Phase-37 actuator machinery to make it actually useful —
**real write-capable connectors** behind a per-connector permission manifest, and **live
in-meeting proposals**. Grounded in the existing seams: the executor takes an injected
`connector(proposal) -> dict` (Phase 37); `connector_runtime.PermissionGate` already gates
`run_subprocess` (`shell:exec`) + `open_outbound_socket` (`network:outbound`);
`connector_sdk.ConnectorManifest` already carries `permissions`/`requires_network`; and the
live event path is `WebRuntime` `server.broadcast(type, data)` (via the `MeetingSession`
`on_broadcast` inversion). Not started — HS-38-01 is the entry point.)

## Goal

Phase 37 proved actuators are **safe**: an actuator proposes, a human approves, a guarded
executor acts only under the gate + payload parity + audit. But it shipped **dormant** —
one reference actuator writing a local file, approval only on the saved-meeting detail.
Phase 38 makes the mechanism **useful**, without weakening a single guarantee:

1. **Real write connectors.** Today the executor's connector is injected and the only
   built-in connector pack (`github_cli`) is **read-only by Phase-25 policy**. Add a
   **gated write-connector framework** — a connector declares exactly which writes it may
   perform (a per-connector **permission manifest**), and every outbound call routes
   through `PermissionGate` (`shell:exec` for CLI, `network:outbound` for HTTP). Ship two
   concrete references: a **GitHub** write connector (`gh issue create`) and a **webhook**
   connector (HTTP POST to an allow-listed host — covers Slack incoming webhooks).
2. **Live in-meeting proposals.** Today proposals surface only when you open a saved
   meeting. Surface them **during** an in-progress meeting: broadcast on a new proposal,
   show a live "pending actions" panel, and approve/reject live — all still behind the
   same gate (actuators off by default; nothing runs without approval).

The invariant from Phase 37 is unchanged and load-bearing throughout:

> **No external side effect without an explicit, audited, per-action human approval —
> and what executes is exactly what was previewed.**

Every new connector adds a *narrower* gate (its permission manifest), never a looser one.

## Scope

### In

- **Gated write-connector framework + permission manifest (HS-38-01).** A connector-author
  contract for *write* actuator connectors: a per-connector manifest declaring the exact
  permitted operations (e.g. `gh issue create` argv prefixes; allow-listed webhook hosts)
  + the `PermissionGate` permission it needs (`shell:exec` / `network:outbound`). A
  `build_gated_connector(...)` helper that wraps a side-effect in the gate + the manifest
  allow-check and returns the `connector(proposal) -> dict` the `ActuatorExecutor` expects.
  Anything the manifest doesn't admit is refused **before** egress. Unit-tested with a fake
  gate/runner (no real egress).
- **GitHub write connector — `gh issue create` (HS-38-02).** The first concrete write
  connector, `shell:exec` via `PermissionGate.run_subprocess`, manifest-allow-listed to
  `gh issue create` only. Re-point `followup_ticket_actuator` (or a sibling) at it behind
  the gate; opt-in test with an injected runner (deterministic, no real `gh`); a real run
  documented if a target repo is reachable.
- **Webhook write connector — HTTP POST (HS-38-03).** The `network:outbound` reference: a
  POST to an **allow-listed host** (covers Slack/Teams incoming webhooks + generic
  endpoints). Manifest declares the permitted host(s); the gate enforces
  `network:outbound`. A `webhook_post_actuator` proposing a message; opt-in test with an
  injected HTTP client.
- **Live in-meeting proposals + broadcast (HS-38-04).** When an actuator proposes during a
  live meeting, **broadcast** it (`server.broadcast("actuator_proposed", …)` via the
  `MeetingSession` → `WebRuntime` seam) so the live dashboard shows a "pending actions"
  panel; approve/reject **live** (reusing the HS-37-03 decision API). Default off; nothing
  runs without approval; the saved-meeting approval surface is unchanged.
- **Actuators II documentation (HS-38-05).** Extend `docs/PLUGIN_AUTHORING.md` (and the
  connector guide if relevant) with **write connectors** — the permission manifest, the
  two reference connectors, the gate mapping — and **live proposals**; reconcile any live
  doc that implies actuators only write locally / only approve post-meeting. Doc
  drift-guard + link-check green. (Dedicated docs story.)
- **Closeout (HS-38-06).** Egress-posture review extended to the new write paths (every
  connector is manifest-gated + permission-gated + still approval-gated + audited);
  demo capture; `final-summary.md`; README phase row → done; HANDOVER refresh.

### Out

- **Reworking the Phase-37 safety machinery** — the contract / lifecycle / executor / audit
  are unchanged; this phase adds *connectors* and a *surface*, each a narrower gate.
- **OAuth / credential management UI** — connectors use existing local auth (`gh` already
  authenticated; a webhook URL is a config value). No secret-store this phase.
- **Autonomous / unattended execution** — every side effect still needs a human approval.
- **Multi-step / chained actions** (an actuator triggering another) — still out.
- **More than the two reference connectors** — jira/linear/etc. are the same pattern
  (a CLI or webhook connector + a manifest), documented as such, not all built here.

## Exit criteria (evidence required)

- [ ] A write actuator connector declares a **permission manifest**; every outbound call
      routes through `PermissionGate` and anything the manifest doesn't admit is refused
      **before** egress (unit-tested with a fake gate — no real egress). (HS-38-01)
- [ ] The **GitHub** connector performs `gh issue create` only, behind `shell:exec` + the
      manifest; an opt-in test drives the full loop with an injected runner (no real `gh`
      in CI). (HS-38-02)
- [ ] The **webhook** connector POSTs only to an allow-listed host, behind
      `network:outbound` + the manifest; an off-list host is refused. (HS-38-03)
- [ ] Actuator proposals **broadcast live** and are approvable from the live dashboard;
      default off; nothing runs without approval; the saved-meeting surface still works.
      (HS-38-04)
- [ ] `docs/PLUGIN_AUTHORING.md` documents write connectors (permission manifest + the two
      references) + live proposals; no live doc implies actuators are local-only /
      post-meeting-only; doc-guards green. (HS-38-05)
- [ ] Egress-posture review extended to the write paths; demo captured; `final-summary.md`;
      README → done. (HS-38-06)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; routing
      invariants unchanged (actuators stay off + unregistered by default); the default
      suite makes **no real outbound call**. (all)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-38-01 | Gated write-connector framework + permission manifest | done | [story-01-write-connector-framework.md](./story-01-write-connector-framework.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-38-02 | GitHub write connector (`gh issue create`) | done | [story-02-github-connector.md](./story-02-github-connector.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-38-03 | Webhook write connector (HTTP POST, allow-listed host) | done | [story-03-webhook-connector.md](./story-03-webhook-connector.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-38-04 | Live in-meeting proposals + broadcast | not-started | [story-04-live-proposals.md](./story-04-live-proposals.md) | — |
| HS-38-05 | Actuators II documentation | not-started | [story-05-documentation.md](./story-05-documentation.md) | — |
| HS-38-06 | Closeout + final-summary | not-started | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

**HS-38-03 done 2026-06-04** — the `network:outbound` reference connector is in.
`holdspeak/plugins/builtin/webhook_post_actuator.py` ships `WebhookPostActuator` (proposes an
HTTP POST `{url, body}`; pure `run()`) and `build_webhook_connector` (built on HS-38-01:
manifest allow-listed to the **config host allow-list**, `network:outbound` through
`PermissionGate.open_outbound_socket`; an off-list host is refused before egress, a non-2xx /
transport error → `failed` + audit, the status returned). The HS-38-01 host-granularity
deferral is **resolved**: `MeetingConfig.webhook_allowed_hosts` (default-empty ⇒ nothing
posts). Both gate kinds are now proven on the framework. **Next: HS-38-04** — live in-meeting
proposals (broadcast `actuator_proposed` + a live approve/reject panel).

**HS-38-02 done 2026-06-04** — the `shell:exec` reference connector is in.
`holdspeak/plugins/builtin/github_issue_actuator.py` ships `GithubIssueActuator` (proposes a
GitHub issue for the first unowned action item; payload `repo`/`title`/`body`; pure `run()`)
and `build_github_issue_connector` (built on HS-38-01: manifest allow-listed to **`gh issue
create` only**, `shell:exec` through `PermissionGate`, argv from the stored payload, a
non-zero exit → `failed` + audit, the issue URL returned). It's a host-side gated connector
(executor injects it, not a discovered pack), opt-in + off by default. **Next: HS-38-03** —
the webhook connector (the `network:outbound` reference: HTTP POST to an allow-listed host).

**HS-38-01 done 2026-06-04** — the safety seam. `holdspeak/plugins/gated_connector.py` ships
`WriteConnectorManifest` (one egress permission + a concrete argv-prefix / host allow-list;
an empty allow-list admits nothing), `GatedOperation` (a planned subprocess/outbound side
effect), `ConnectorOperationRefused`, and `build_gated_connector` (**plan → allow-check →
gate → interpret**; the allow-check refuses before the `PermissionGate` is touched). It
reuses the Phase-13 `PermissionGate` (no second egress primitive) and the Phase-37
`ActuatorExecutor` is unchanged.

**Scaffolded 2026-06-04**, right after Phase 37 closed (merged via PR #14). The recon is
done — the seams all exist:

- **Executor seam (Phase 37):** `ActuatorExecutor(db, connector=…)` takes any
  `connector(ActuatorProposal) -> dict`. The new write connectors are just gated
  `connector` callables — the executor (status + policy + parity + audit) is unchanged.
- **Permission gate:** `holdspeak/connector_runtime.py` `PermissionGate` —
  `run_subprocess` requires `shell:exec`, `open_outbound_socket` requires
  `network:outbound` (`_OPERATION_PERMISSIONS`); tests inject a fake runner. This is the
  egress chokepoint every write connector routes through.
- **Permission manifest:** `holdspeak/connector_sdk.py` `ConnectorManifest` already carries
  `permissions` / `requires_network` / `capabilities`; the `github_cli` pack's
  `is_command_allowed` (read-only `gh pr/issue view`) is the allow-list precedent to mirror
  for a *write* policy.
- **Live broadcast:** `WebRuntime` calls `self.server.broadcast(message_type, data)` and
  observes `MeetingSession` live events via the `on_broadcast` inversion
  (`_on_meeting_broadcast`); existing live events are `intel_status` / `segment` /
  `intel_complete` / `meeting_updated`. A new `actuator_proposed` broadcast fits this path.
- **Approval API/UI (Phase 37):** `POST /api/meetings/{id}/proposals/{pid}/decision` + the
  "Proposed actions" cards — reused live in HS-38-04.

## Pickup order

1. ~~**HS-38-01** — gated write-connector framework + permission manifest. The safety seam
   every connector depends on.~~ **done 2026-06-04.**
2. ~~HS-38-02 — GitHub write connector (`shell:exec` reference).~~ **done 2026-06-04.**
3. ~~HS-38-03 — webhook write connector (`network:outbound` reference).~~ **done 2026-06-04.**
4. HS-38-04 — live in-meeting proposals + broadcast. **◀ next**
5. HS-38-05 — Actuators II documentation.
6. HS-38-06 — closeout + final-summary.

01 → 02/03 is the connector half (01 is the framework; 02 and 03 are two concrete proofs,
one per gate type — they can go in either order). 04 is the live-surface half (independent
of the connectors; needs the Phase-37 approval API). 05 documents the stable surface; 06
records. Keep actuators **off + unregistered by default** so routing/dispatch stays
byte-identical, and keep the default suite free of any real outbound call (inject
runners/clients).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A write connector egresses beyond its manifest | High if careless | Every outbound call routes through `PermissionGate` + the manifest allow-check; anything not admitted is refused before egress; unit-tested with a fake gate | A connector performs an op its manifest didn't declare |
| The default suite makes a real outbound call | Medium | Inject the subprocess runner / HTTP client in tests; real `gh`/webhook runs are opt-in + skipped in CI | CI does a real `gh issue create` or HTTP POST |
| Live proposals leak / auto-execute | Medium | Broadcasting a proposal is not approving it; live approve reuses the same gated decision endpoint; actuators off by default | A live proposal executes without a recorded approval |
| Scope creep into OAuth / a secret store / many connectors | Medium | Two reference connectors only; reuse existing local auth + a config webhook URL; others documented as the same pattern | A PR adding a credential vault or a third connector |
| Weakening the Phase-37 guarantees to fit a connector | High (tempting) | The contract/lifecycle/executor/audit are **out of scope**; connectors are narrower gates layered on, never looser | A connector that bypasses the executor or skips the manifest |

## Decisions made (this phase)

- 2026-06-04 — **Direction = Actuators II** (real write connectors + live proposals) —
  user pick over Release/First-Run, Dogfood/Reliability, and UX-consolidation.
- 2026-06-04 — **Two reference connectors, one per gate type** (`gh issue create` for
  `shell:exec`, a webhook POST for `network:outbound`) — proves both egress kinds; jira/
  linear/etc. are the same pattern, documented not built.

## Decisions deferred

- ~~**Webhook host allow-listing granularity**~~ — **resolved HS-38-03 (2026-06-04):** a
  config allow-list of hosts (`MeetingConfig.webhook_allowed_hosts`, default-empty); a
  proposal's target host must be a member, vetted by the connector manifest before egress.
- **Where live actuators generate** — reuse finalization-time dispatch vs a live dispatch
  tick — trigger: HS-38-04 design — default: surface proposals as soon as they're produced
  by the existing dispatch path; a dedicated live-dispatch cadence is a follow-up if needed.
- **Whether the GitHub write connector is its own pack vs a host-side connector** — trigger:
  HS-38-02 — default: a host-side gated connector (the executor injects it), mirroring the
  Phase-37 `build_outbox_connector`, not a discovered pack.
