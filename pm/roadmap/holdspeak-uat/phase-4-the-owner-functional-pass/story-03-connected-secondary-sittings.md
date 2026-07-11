# HSU-4-03 — Connected + secondary target sittings

- **Project:** holdspeak-uat
- **Phase:** 4
- **Status:** backlog
- **Depends on:** HSU-4-02
- **Owner:** owner (verdicts) + agent (debrief/triage)

## Problem

Connected integrations and separately built native shells are real functional
surfaces, but they have larger preflights and can obscure the flagship/daily-use
result. They need a separately labeled extension.

## Scope

- Campaign 6: sync, mesh, companion handoff, external proposals/connectors, and
  delivery-belt actions, using only disposable external targets.
- Campaign 7: companion/classic-only surfaces, conditional on intentionally
  installed exact builds.
- Keep all results bound to their actual implementation target and form factor.
  A cross-device journey is multiple qualified legs, not one generic surface
  verdict copied across React and Swift.

## Acceptance criteria

- [ ] Campaign 6 has a completed, fully triaged debrief.
- [ ] External-action evidence names only the disposable preflight targets.
- [ ] Campaign 7 is either completed against exact builds or explicitly omitted
      as conditional; no result is credited to `ios_flagship_swift`.
- [ ] Every native result has a matching bundle/build/device/OS/install-source
      attestation with pairing verified; React browser evidence stays separate.

## Test plan

- Manual/device/network: the guided campaigns and their recorded preflight.
- Evidence: sitting debriefs, connector receipts against throwaway targets, and
  exact native build notes.
