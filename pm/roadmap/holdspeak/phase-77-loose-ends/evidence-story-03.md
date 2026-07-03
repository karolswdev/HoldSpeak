# Evidence — HS-77-03 — The coders-status conflation dies

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-77-loose-ends`)

## What changed

- **Consumers verified FIRST** (the exit criterion's order): the iPad's
  `CompanionStatusDTO` never decoded the `connectors` block (it reads
  `agent.sessions` only), its desk connector tiles are locally defined,
  and the web's `slack_configured` gating reads the AFTERCARE payload.
  The block was a dead contract with living tests.
- **The domain owns its status now**: `GET /api/desk/actuators/status`
  returns the three configured booleans (URLs are credentials and never
  ride a payload — the HSM-14 rule, kept verbatim). The docstring records
  the conflation's history.
- **`/api/coders/status` reports coder sessions only** — the config-load
  block and the `connectors` payload key are gone.
- The three integration tests that pinned the old location migrated to
  the new route (they were the block's only real consumers).

## Verification artifacts

- The companion/coders test slice: **53 passed** (the three migrated
  tests exercising off→on for each connector against the real routes).
- One authoring misstep caught by the run: the new route's handler-local
  `Config` import was missing (the except swallowed the NameError into
  all-False — exactly the failure shape the honest-flags tests exist to
  catch).
- API manifest regenerated (guard 5/5). Full suite: **3095 passed, 37
  skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] Consumers verified before the removal; the flags kept a home in
      their own domain; coders-status is sessions-only.
