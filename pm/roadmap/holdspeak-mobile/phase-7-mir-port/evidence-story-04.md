# Evidence — HSM-7-04 — Profile-effect gate closeout (Track-H gate)

- **Shipped:** 2026-06-19 · **Branch:** `holdspeak-mobile/phase-7-mir-port`

## The gate — PASSED

Control-vs-treatment over **one identical transcript** (mixed architecture +
incident + product content), holding everything constant except the profile, with a
deterministic fake provider so the measured difference is purely the routing:

```
balanced  → {action_items, adr, customer_signals, decisions, incident_timeline, requirements, risk_register}
architect → {adr, customer_signals, decisions, dependency_map, incident_timeline, requirements}
delta (symmetric difference) → {action_items, dependency_map, risk_register}
```

**Metric:** artifact-type set symmetric difference. **Result:** non-empty (3 types) —
switching the profile measurably changes the extracted artifact set. (Both profiles
also picked up `customer_signals` + `incident_timeline` from the off-profile intents
scored in the transcript — the score-driven additions working.)

## Verification
`testGateProfileChangesExtraction` (RuntimeCoreTests/MIRRouterTests) asserts the
delta is non-empty and both runs produce artifacts. Deterministic + reproducible.
`swift test` **69 / 6 skipped / 0 failures**. Closes Phase 7 (see `final-summary.md`).
