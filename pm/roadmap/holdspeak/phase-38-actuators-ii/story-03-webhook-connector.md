# HS-38-03 — Webhook write connector (HTTP POST, allow-listed host)

- **Project:** holdspeak
- **Phase:** 38
- **Status:** not-started
- **Depends on:** HS-38-01
- **Unblocks:** HS-38-05
- **Owner:** unassigned

## Problem

The second reference connector exercises the *other* gate — `network:outbound` — and is the
most reusable: an HTTP POST to an **allow-listed host** covers Slack/Teams incoming
webhooks and generic endpoints. It proves the framework handles network egress as tightly
as it handles subprocess egress.

## Scope

- **In:**
  - A **webhook connector** built with `build_gated_connector` (HS-38-01): permission
    `network:outbound` via `PermissionGate.open_outbound_socket` (or the gate's HTTP op),
    manifest declaring the **allow-listed host(s)**. The connector POSTs the proposal's
    message payload (JSON) to the target URL; a target host **not** on the allow-list is
    refused before egress. Returns the response status as the result; a non-2xx / transport
    error → raises → `failed` + audit.
  - A `webhook_post_actuator` whose proposal carries `{url, body}` (e.g. "post the
    stakeholder update to the comms webhook"). Host allow-list comes from config (default:
    a `MeetingConfig` webhook allow-list; resolve granularity here).
  - An **opt-in** test driving the loop with an **injected HTTP client** (deterministic, no
    real network); plus an off-list-host refusal test.
- **Out:**
  - Slack/Teams *API* clients (OAuth, rich blocks) — a plain incoming-webhook POST only.
  - Retry/backoff beyond the executor's manual retry.

## Acceptance criteria

- [ ] The connector POSTs only to an **allow-listed host**; an off-list host is refused
      **before** egress (the HTTP client is never invoked).
- [ ] Full loop (opt-in, injected client): approve → execute → `executed` + the response
      status in the result + audit; a non-2xx → `failed` + audit.
- [ ] The host allow-list is config-driven (decided here) and default-empty ⇒ nothing posts.
- [ ] Default suite makes no real HTTP call; suite green; module ruff + F821 clean.

## Test plan

- Unit: allow-list check (on-list permitted, off-list refused, default-empty refuses all).
- Unit (loop): injected client returns 200 → `executed`; returns 500 / raises → `failed` +
  audit.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- Decision (resolve here, deferred from HS-38-01): host allow-listing granularity — default
  a config allow-list of hosts (`MeetingConfig`), a proposal's target host must be a member.
- This connector is the template the docs (HS-38-05) point at for "any HTTP endpoint";
  Slack/Teams are incoming-webhook URLs on the allow-list, not bespoke integrations.
