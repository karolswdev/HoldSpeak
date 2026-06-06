# Evidence — HS-42-05 — Trust & Privacy (ambient chip + panel)

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

The local-first posture is now **ambient** — a persistent shell chip on every
route (the refinement that pairs the privacy story with the Phase-41 ambient
presence philosophy), opening a full Trust & Privacy panel.

### The chip — `web/src/components/TrustChip.astro`

A persistent shell-header button (shield glyph + tone-keyed dot + label) that
replaces the static `LocalPill` as the TopNav default. It shows the **single
highest-priority posture** read from `GET /api/setup/status` `trust{}`:

- **Local only** (default) · **Configured endpoint** (a transcript can reach a
  configured endpoint) · **Writes need approval** (actuators on) · **Needs
  attention** (off-loopback bind with no auth token).

The chip renders an honest "Local only" server-side; the shell script fills the
live posture on load (best-effort — a status failure leaves the honest default).

### The view-model — `web/src/scripts/trust-view.js`

Pure, exported, DOM-free: `trustPosture(trust)` → the chip posture, and
`trustRows(trust, presence)` → the panel breakdown. Kept pure so the rules are
unit-testable independent of the page.

### The panel — `AppLayout.astro`

A right-side dialog (opened from the chip; Esc/backdrop close) with plain-language
rows answering **"what can leave this machine right now?"** — Web runtime
(loopback + auth), Transcript egress (+ the configured endpoint), Actuators
(approval-gated), Webhook hosts (allow-list), Desktop presence — each tone-keyed,
with a "nothing leaves without you configuring it" footer linking to Settings.
Config values are rendered via `textContent` (never `innerHTML`).

## Verification

- **Posture mapping (Node harness over the real module):**

  ```
  PASS  local default          -> Local only [local]
  PASS  cloud endpoint         -> Configured endpoint [info]
  PASS  actuators on           -> Writes need approval [warn]
  PASS  off-loopback no auth   -> Needs attention [danger]
  PASS  off-loopback with auth -> Local only [local]
  rows: 5 · Web runtime · Transcript egress · Actuators · Webhook hosts · Desktop presence
  TRUST-VIEW HARNESS OK
  ```

- **Live (Playwright, two real configs):** the chip read `Local only` on a
  default config and `Configured endpoint` on a cloud-intel config; the panel
  opened with the correct rows.
  Screenshots: [`evidence/trust_local.png`](./evidence/trust_local.png) and
  [`evidence/trust_cloud.png`](./evidence/trust_cloud.png) (the panel showing the
  configured `http://homelab.local:8000/v1` endpoint).

## Tests run

```
uv run pytest -q tests/integration/test_web_trust_chip.py
→ 2 passed
```

- `test_shell_carries_the_trust_chip_and_panel` — the shell HTML has the chip
  (`data-trust-open`), the panel (`id="trust-panel"`), the honest default, and
  the rows container (build-agnostic).
- `test_trust_view_module_maps_postures` — locks the posture rule strings in
  `trust-view.js` (the Node harness asserts the live mappings).

The underlying `trust{}` data (local/cloud/actuator variants) is Python-tested in
HS-42-01 (`test_setup_status.py`). Full suite: see the commit message.

## Acceptance criteria

- [x] A persistent shell chip shows posture on every route and opens the panel;
      its state maps correctly from `trust{}` — Node harness (5 cases) + a live
      two-config Playwright check.
- [x] The panel answers the listed questions in plain language (web bind/auth,
      egress + endpoint, actuators, webhook hosts, presence) with a Settings link.
- [x] Status mapping tested for local / cloud / actuator / off-loopback
      permutations.
- [x] Bundle rebuilt; only `web/src` committed; screenshots of default local-only
      and a configured-endpoint state.
- [x] Default suite green; default (local-only) posture is the honest default.
