# HSM-7-02 — The five profiles

- **Project:** holdspeak-mobile
- **Phase:** 7
- **Status:** backlog
- **Depends on:** HSM-7-01
- **Unblocks:** HSM-7-04
- **Owner:** unassigned

## Problem

The charter names five MIR profiles — Balanced, Architect, Delivery, Product,
Incident — and the gate requires each to shape extraction distinctly. Without
distinct per-profile emphasis mapped onto MIR-01's intent vocabulary, the profiles
are cosmetic and the gate fails.

## Scope

- **In:** the five profiles defined with their per-profile artifact emphasis,
  mapped onto MIR-01's intent set (`architecture`, `delivery`, `product`,
  `incident`, `comms`); a profile-emphasis assertion that each non-Balanced
  profile's emphasis differs from Balanced's.
- **Out:** the routing engine (HSM-7-01). The selection seam (HSM-7-03). The gate
  demonstration (HSM-7-04). Inventing intent labels outside the MIR-01 set.

## Acceptance criteria

- [ ] All five profiles exist with a documented, distinct emphasis mapping onto
      MIR-01's intent vocabulary (verbatim labels, no invented intents).
- [ ] A test asserts each of Architect/Delivery/Product/Incident has an emphasis
      that differs from Balanced (the profiles aren't aliases).
- [ ] Balanced is the neutral default and matches the desktop's balanced behavior.
- [ ] Any intent a profile needs that isn't in the MIR-01 set is recorded as a
      proposed canon addition, not silently added.

## Test plan

- Unit: load each profile → assert its emphasis mapping; assert pairwise that
  non-Balanced profiles differ from Balanced.
- Manual: cross-check the five against the MIR-01 canon's intent set.

## Notes / open questions

- The Architect profile pairs with Phase-6 ADR Candidates (HSM-6-03); Incident
  with risk/decision emphasis; keep these mappings faithful to MIR-01 for
  cross-runtime parity.
- Emphasis is data (profile → intent weights/chains), not code branches, so a new
  profile is a config addition later.
