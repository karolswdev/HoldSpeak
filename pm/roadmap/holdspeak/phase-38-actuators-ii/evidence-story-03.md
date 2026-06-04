# Evidence — HS-38-03: Webhook write connector (HTTP POST, allow-listed host)

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

The second reference connector — and the most reusable. It exercises the *other* gate,
`network:outbound`: an HTTP POST to an **allow-listed host**, which covers Slack / Teams
incoming webhooks and any generic endpoint. The framework now gates network egress as
tightly as it gates subprocess egress.

### Files

- **`holdspeak/plugins/builtin/webhook_post_actuator.py` (new)** — the same two-half split:
  - **`WebhookPostActuator`** (`kind=actuator`, cap `["actuator"]`) — `run(context)` proposes
    a webhook POST; payload carries `{url, body}` (url from `context["webhook_url"]`, body a
    Slack-shaped `{"text": …}` meeting update). Pure: no `webhook_url` (or a URL with no host)
    raises → the host records a plain `error`. `reversible=False` (a posted message can't be
    unsent).
  - **`build_webhook_connector(*, allowed_hosts, client=…, timeout_seconds=…)`** —
    `build_gated_connector` with a `WriteConnectorManifest` (permission `network:outbound`,
    `allowed_hosts=tuple(allowed_hosts)`), a `plan` that derives the target `(host, port)` +
    the request `{url, body}` from the stored payload, and an `interpret` that raises on a
    non-2xx status (→ executor `failed` + audit) else returns `{status, host}`. The POST
    routes through `PermissionGate.open_outbound_socket` (the opener closure carries the full
    op so the HTTP client sends `op.request`). `client` defaults to a urllib POST
    (`_default_post`; converts an `HTTPError` to a `WebhookResponse` so non-2xx flows through
    `interpret` uniformly); tests inject a fake.
  - **`WebhookResponse`** (`status`, `body`); **`register_webhook_post_actuator`** — opt-in,
    **not** in `register_builtin_plugins`.
- **`holdspeak/config.py`** — `MeetingConfig.webhook_allowed_hosts: list[str]` (default `[]`),
  normalized in `__post_init__` like `allowed_actuators` but **lowercased** (DNS is
  case-insensitive); a non-list raises.

### Decision resolved (deferred from HS-38-01): host allow-listing granularity

A **config allow-list of hosts** — `MeetingConfig.webhook_allowed_hosts`. A proposal's target
host must be a member; the list is **default-empty**, so a misconfigured webhook actuator
posts nowhere. Slack/Teams are just incoming-webhook URLs whose host is on the allow-list —
not bespoke API integrations (no OAuth, no rich blocks; a plain incoming-webhook POST only).

### Why this is safe

- **Allow-listed host only.** The manifest refuses a target host not on `allowed_hosts`
  **before** egress — the HTTP client is never invoked (asserted with a client spy). An empty
  allow-list refuses everything.
- **Off by default** — opt-in + capability-blocked + reached only after approval + the
  `allow_actuators` policy gate + payload parity + `network:outbound`. Like the other
  connectors it's a host-side gated connector the executor injects (not a discovered pack);
  no production runtime constructs an `ActuatorExecutor` yet (live execution is HS-38-04).

## Verification

### Targeted — actuator + connector + config + full loop

```
$ uv run pytest -q tests/unit/test_webhook_post_actuator.py
13 passed in 0.43s
```

- **Faithful proposal** — `target=webhook` / `action=post_message` / payload `{url, body}`,
  preview names the host; no `webhook_url` → `error`; capability off → `blocked`.
- **Allow-list (config-driven)** — posts to an allow-listed host (client receives the url +
  body); an off-list host raises `ConnectorOperationRefused` with the client never invoked; a
  default-empty allow-list refuses all; the list is `MeetingConfig.webhook_allowed_hosts`
  (normalized — the connector is built from it).
- **Full loop (injected client)** — execute-before-approval refused (no POST); approve →
  execute → `executed` with `{status: 200, host}` + audit `proposed→approved→executed`; a 500
  → `failed` + audit (error carries `HTTP 500`); a transport error (client raises) → `failed`.
- **Config validation** — `webhook_allowed_hosts` defaults empty, lowercases + dedupes, and
  rejects a non-list.
- **Default set** — `webhook_post_actuator` is not in `register_builtin_plugins`.

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2117 passed, 15 skipped in 60.70s        # +13 vs HS-38-02 (the new webhook tests)
$ uv run ruff check holdspeak/plugins/builtin/webhook_post_actuator.py tests/unit/test_webhook_post_actuator.py holdspeak/config.py
All checks passed!
$ uv run ruff check --select F821 holdspeak/plugins/builtin/webhook_post_actuator.py
All checks passed!
```

The default suite makes **no real HTTP call** — every test injects a fake client.

## Notes

- This connector is the template HS-38-05 docs will point at for "any HTTP endpoint": a
  Slack/Teams incoming webhook is simply a URL whose host the operator adds to
  `webhook_allowed_hosts`. Rich blocks / OAuth APIs are explicitly out of scope.
- Both reference gates are now proven on the HS-38-01 framework: `shell:exec` (HS-38-02
  `gh issue create`) and `network:outbound` (this story). jira/linear/etc. are the same
  pattern — a CLI or webhook connector + a manifest — documented in HS-38-05, not built.
