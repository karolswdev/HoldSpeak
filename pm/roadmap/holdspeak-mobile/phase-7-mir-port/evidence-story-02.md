# Evidence — HSM-7-02 — The five profiles

- **Shipped:** 2026-06-19 · **Branch:** `holdspeak-mobile/phase-7-mir-port`

## What
`MIRRouter.baseEmphasis` defines the five charter profiles' per-profile artifact
emphasis (distinct ordered `ArtifactType` chains), over MIR-01's intent set:

- **balanced** → decisions, action_items, risk_register, requirements
- **architect** → adr, decisions, dependency_map, requirements
- **delivery** → milestone_plan, action_items, risk_register, decisions
- **product** → requirements, customer_signals, scope_review, decisions
- **incident** → incident_timeline, runbook_delta, risk_register, action_items

Off-profile intents above threshold contribute their signature artifact
(`intentSignature`), so content also shapes the chain.

## Verification
`testEveryProfileExistsAndDiffersFromBalanced` — all five profiles present; every
non-balanced emphasis differs from balanced; `MIRProfile.allCases.count == 5`.
`swift test` 69 / 6 skipped / 0 failures.
