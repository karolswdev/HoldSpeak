# Evidence — HS-38-05: Actuators II documentation

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

The authoring docs now describe the real Phase-38 surface — **write connectors** behind a
permission manifest, and **live in-meeting approval** — so an author can write a *write*
connector safely and a user understands the live surface. The stale "actuators only write a
local file / approve post-meeting" framing is reconciled. (Dedicated docs story — the
standing per-phase practice; mirrors HS-37-06's contract → gates → worked-example → testing
shape.)

### `docs/PLUGIN_AUTHORING.md`

- **New `### Write connectors (the permission manifest)` subsection** (under Actuators, after
  the outbox worked example): why a real-system connector still must not exceed what it
  declared; `WriteConnectorManifest` (one permission + a concrete allow-list; empty admits
  nothing); the **gate-mapping table** (`shell:exec`→`run_subprocess`→`allowed_argv_prefixes`;
  `network:outbound`→`open_outbound_socket`→`allowed_hosts`); `build_gated_connector`'s
  **plan → allow-check → gate → interpret** order (a refused op raises
  `ConnectorOperationRefused` *before* egress); and **both reference connectors as worked
  examples** — `gh issue create` (`shell:exec`, no-shell ⇒ no injection, auth = local `gh`)
  and the webhook POST (`network:outbound`, `MeetingConfig.webhook_allowed_hosts`
  default-empty, Slack/Teams = an allow-listed URL). Linked to the real modules + their
  injected-runner/client tests.
- **New `### Live proposals` subsection:** the read-only `actuator_proposed` broadcast (id +
  lifecycle + preview — never the egress payload), the live "Pending actions" panel, and that
  live approval reuses the *same* decision endpoint (a surface, not a new execution path;
  default off). Linked to `test_live_proposals.py`.
- **Reconciled framing:** the guarded-executor connector paragraph now points at
  `build_gated_connector` (route through the `PermissionGate`, don't invent an outbound path)
  instead of "route it through `connector_runtime`"; the outbox worked example is reframed as
  "the simplest connector," not the only one; the **reference table** gains
  `github_issue_actuator` + `webhook_post_actuator` rows; the config addition (the webhook
  host allow-list) is documented inline in the webhook example.

### `README.md`

- The plugin-section actuator paragraph no longer says "one reference actuator … as the
  worked example"; it now names **real write connectors** (GitHub issue, webhook POST) behind
  a permission manifest and **live** approval, still off by default.

## Verification

- **Doc-truth reconciliation** — grepped live docs for `actuator` / `outbox`; the only live
  doc with actuator framing is `docs/PLUGIN_AUTHORING.md` (+ the README paragraph), both
  updated. Frozen PMO/evidence history left verbatim.
- **Worked examples match the code** — API/field names verified against the shipped modules
  (`gated_connector.WriteConnectorManifest`/`build_gated_connector`,
  `github_issue_actuator.build_github_issue_connector`,
  `webhook_post_actuator.build_webhook_connector`, `MeetingConfig.webhook_allowed_hosts`).
- **Doc-guards + link-check green; all new relative links resolve:**

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py -k "drift or link or dangling"
3 passed
$ uv run pytest -q -k doc --ignore=tests/e2e/test_metal.py
55 passed, 1 skipped, 2082 deselected
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2123 passed, 15 skipped in 61.23s        # docs-only — unchanged from HS-38-04
```

The new heading `### Write connectors (the permission manifest)` resolves to the in-page
anchor `#write-connectors-the-permission-manifest` used by the two cross-links.

## Notes

- Documentation only — no behavior change (suite count unchanged).
- The connectors guide (`docs/CONNECTOR_DEVELOPMENT.md`) describes *activity* connector packs
  (discovery/enrichment), a different surface from the host-side actuator connectors; it
  needed no change. The write-connector docs live with the actuator authoring section, which
  is where an actuator author looks.
