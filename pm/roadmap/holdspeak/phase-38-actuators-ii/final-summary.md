# Phase 38 — Actuators II — Final Summary

**Status:** CLOSED ✅ — 6/6 stories shipped. **Closed:** 2026-06-04.

Phase 37 proved actuators are **safe** but shipped them **dormant** — one reference actuator
writing a local file, approval only on the saved-meeting detail. Phase 38 makes the
mechanism **useful** without weakening a single guarantee: **real write connectors** (file a
GitHub issue, POST to a webhook) behind a per-connector **permission manifest**, and **live
in-meeting proposals**. The Phase-37 invariant is unchanged and load-bearing throughout:

> **No external side effect occurs without an explicit, audited, per-action human approval —
> and what executes is exactly what was previewed.**

Every new connector adds a *narrower* gate (its permission manifest), never a looser one.

## The egress-posture review (the headline)

There is **no code path** by which a Phase-38 write reaches an external system without all of:

1. **A registered, capability-enabled actuator** — `github_issue_actuator` /
   `webhook_post_actuator` are *not* in `register_builtin_plugins`; one must be explicitly
   registered and `actuator` must be in `enabled_capabilities`, or proposing is `blocked`.
2. **A persisted `approved` proposal** — `ActuatorExecutor.execute` refuses anything not
   `approved` (`ActuatorExecutionError`); approval is a deliberate human act (the saved-meeting
   surface **or** the new live panel), recorded with `decided_by` + an audit entry.
3. **The governance gate** — `MeetingConfig.allow_actuators` (master, default `False`) **and**
   membership of `allowed_actuators`; a refusal raises `ActuatorPolicyError` with **no state
   change**. Default-safe: off + empty ⇒ nothing runs.
4. **Payload parity** — the side effect is built from the proposal's stored `payload`; a hash
   mismatch aborts to `failed` with **no outbound call** (TOCTOU guard).
5. **The connector's permission manifest + `PermissionGate`** — *new this phase.* A write
   connector declares one permission (`shell:exec` / `network:outbound`) + a concrete
   allow-list (argv prefixes / hosts). `build_gated_connector` checks the manifest **before**
   the gate; an op the manifest doesn't admit raises `ConnectorOperationRefused` and reaches
   **no** egress. Admitted ops route through the existing `connector_runtime.PermissionGate`
   — no second egress primitive. An empty allow-list admits nothing.
6. **An audit row** — every terminal transition (`executed` / `failed`) is recorded via
   `transition_proposal`, carrying the payload hash.

The **negatives are proven, not asserted** — each produces **no egress** (the spy
runner/client is never called):

- execute **before** approval → `ActuatorExecutionError` (`demo` step 2);
- a non-allow-listed op (`gh repo delete`) → `ConnectorOperationRefused` *before* the gate
  (`demo` step 3; `test_gated_connector` / `test_github_issue_actuator`);
- an **off-list** webhook host → refused before the HTTP client runs
  (`test_webhook_post_actuator`);
- gate off / not allow-listed → `ActuatorPolicyError`, no state change.

**Live proposals add a surface, not a side effect:** the `actuator_proposed` broadcast is
**read-only** (id + lifecycle + preview — never the egress `payload`), and live approve/reject
reuses the *same* gated decision endpoint. **The default suite makes no real outbound call**
— every connector test injects the runner / HTTP client.

Demo (committed, reproducible): `evidence/actuator_write_loop.md` (propose → approve →
execute → audit, with the two negatives; exactly one `gh` call — the executed issue) via
`evidence/demo_write_loop.py`; the live panel in `evidence/live_pending_actions.png` via
`evidence/capture_live_panel.py`.

## What shipped

| Story | Target → result |
|---|---|
| **HS-38-01** | **Gated write-connector framework + permission manifest.** `holdspeak/plugins/gated_connector.py` — `WriteConnectorManifest` (one egress permission + a concrete argv-prefix / host allow-list; empty admits nothing), `GatedOperation`, `ConnectorOperationRefused`, and `build_gated_connector` (**plan → allow-check → gate → interpret**; refuses before the gate). Reuses the Phase-13 `PermissionGate`; the Phase-37 `ActuatorExecutor` unchanged. |
| **HS-38-02** | **GitHub write connector (`shell:exec`).** `github_issue_actuator.py` — proposes a GitHub issue for the first unowned action item; `build_github_issue_connector` runs **`gh issue create` and only that**, argv from the stored payload (no shell ⇒ no injection), a non-zero exit → `failed` + audit, the issue URL returned. Host-side, opt-in. |
| **HS-38-03** | **Webhook write connector (`network:outbound`).** `webhook_post_actuator.py` — proposes an HTTP POST `{url, body}`; `build_webhook_connector` POSTs **only to an allow-listed host** (`MeetingConfig.webhook_allowed_hosts`, default-empty). Resolves the host-granularity deferral. Slack/Teams = an allow-listed URL. |
| **HS-38-04** | **Live in-meeting proposals + broadcast.** `process_meeting_state` gained an `on_proposal` callback (best-effort); `MeetingSession._emit_actuator_proposal` emits a **read-only** `actuator_proposed` broadcast (auto-forwarded by `WebRuntime`); the dashboard shows a Signal "Pending actions" panel with Approve/Reject reusing the Phase-37 decision endpoint — a surface, not a new execution path. |
| **HS-38-05** | **Actuators II documentation** (dedicated story). `docs/PLUGIN_AUTHORING.md` — a **Write connectors (the permission manifest)** subsection (manifest + gate-mapping table + `build_gated_connector` + both references as worked examples) and a **Live proposals** subsection; stale "local-only / post-meeting-only" framing reconciled (README too). |
| **HS-38-06** | Closeout — the extended egress-posture review, the write-loop + live-panel demos, this summary. |

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **2,123 passed, 15 skipped** (+43 over the Phase-37 close: 12 framework + 12 GitHub + 13
  webhook + 6 live). The Phase-38 actuator stack (framework + two connectors + live + the
  Phase-37 executor/reference/contract/repository): **91** tests.
- **Routing invariants intact:** no actuator is registered by default and none is in a router
  chain, so `test_intent_router` / `test_intent_dispatch` / `test_intent_pipeline` /
  `test_multi_intent_routing` are unchanged and green (**38 passed**). `on_proposal` is
  additive + dormant (no actuator chained ⇒ no broadcast).
- **No silent egress, by construction** — see the review above; the default suite makes **no
  real `gh` / HTTP call** (injected runners/clients throughout).
- **Bundle:** `holdspeak/static/_built/` is a gitignored build product — rebuilt to verify,
  **0 files tracked**; only `web/src/**` source committed.
- **Docs:** `docs/PLUGIN_AUTHORING.md` (write connectors + live proposals) + the README
  paragraph; doc drift-guard + live-doc link-check green.
- **Branch:** `phase-38/hs-38-01-write-connector-framework` (phase scaffold + 6 story commits).

## Decisions of record

- **A write connector is a *narrower* gate, never a looser one** — the permission manifest
  layers **under** approval + policy + parity; it can only ever restrict what reaches the wire.
- **Reuse `PermissionGate`, don't add a second egress primitive** — `build_gated_connector`
  synthesizes a minimal `ConnectorManifest` and routes through the Phase-13 gate.
- **Two reference connectors, one per gate type** (`gh issue create` for `shell:exec`, a
  webhook POST for `network:outbound`) — jira/linear/etc. are the same pattern, documented
  not built.
- **Host-side gated connectors, not discovered packs** — the executor injects them, mirroring
  Phase-37's `build_outbox_connector`.
- **Webhook host allow-listing = a config allow-list of hosts** (`MeetingConfig.webhook_allowed_hosts`,
  default-empty); a proposal's target host must be a member.
- **The live broadcast is read-only** — it describes a proposal; it never carries anything
  that could trigger an effect on receipt. Live approval reuses the existing decision endpoint
  (no new execution path).
- **Where live actuators generate** — surface proposals as the existing (finalization-time)
  dispatch produces them; a mid-meeting cadence is a follow-up reusing the same `on_proposal`
  seam.

## Handoff → the next frontier

The actuator mechanism now reaches real systems safely and approves live; the natural
extensions (none committed):

- **More connectors** — jira/linear/Slack-API on the same `build_gated_connector` pattern (a
  CLI or webhook connector + a manifest); or expose write connectors as **discovered packs**
  rather than host-side injection.
- **A cross-meeting approval inbox** — one place to review pending proposals across meetings,
  beyond the per-meeting live panel + saved-meeting detail.
- **A mid-meeting live-dispatch cadence** — generate/surface proposals during the meeting
  (not only at finalization) via the same `on_proposal` → broadcast seam.
- **Per-role governance** (who may approve which actuator) and **multi-step / chained
  actions** — both deliberately out of scope this phase.
