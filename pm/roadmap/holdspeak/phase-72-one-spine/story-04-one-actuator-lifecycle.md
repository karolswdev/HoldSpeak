# HS-72-04 — One actuator lifecycle

- **Status:** todo
- **Priority:** HIGH (a trust-critical path implemented twice is a trust bug waiting)
- **Depends on:** HS-72-03

## Goal

One implementation of propose→approve→execute. Today the lifecycle exists
twice: the meeting proposal path (`meetings.py:936+`) and the desk relay path
(now `desk_actuators.py` after HS-72-03), which fabricates a hidden sentinel
meeting row (`_COMPANION_MEETING_ID = "companion"`) purely to satisfy
`actuator_proposals.meeting_id NOT NULL`. The data model says proposals are
meeting-scoped; two real callers have no meeting. Model the truth: a proposal
has an owner-typed **origin**, and one engine serves every caller.

## Scope

- **In:** an `origin` discriminator on `actuator_proposals`
  (`meeting` | `desk`) with `meeting_id` nullable and enforced-present only
  for `origin='meeting'` (additive migration, `SCHEMA_VERSION` bump, the
  Phase-50 4-way matrix honored — refuse-newer / backup-then-apply re-proven);
  the sentinel meeting row removed and existing sentinel-attached rows
  migrated to `origin='desk'`; one shared lifecycle service (propose, decide,
  execute via `ActuatorExecutor`) called by both routers; audit rows identical
  in shape across origins.
- **Out:** voice macros joining the proposal store (immediate dispatch is the
  Phase-52 design); Slack's inline approve→execute (`allow_actuators=True` at
  the decision route is the Phase-61 design — the shared service preserves
  it); any new connector or approval UI.

## Tasks

- [ ] Schema: add `origin`, relax the FK per above, bump `SCHEMA_VERSION`,
      extend the migration-matrix tests + the schema snapshot (regenerate with
      the identical normalizer regex — the snapshot test's documented quirk).
- [ ] Extract the shared lifecycle service (module under
      `holdspeak/plugins/` or `holdspeak/web/routes/_helpers`, wherever the
      import graph stays acyclic); both routers become thin callers.
- [ ] Delete `_COMPANION_MEETING_ID` and the fabricated-row branch; a
      data-fix migrates any existing sentinel rows.
- [ ] Payload-hash parity, policy re-check, and audit behavior proven
      byte-identical for the meeting path (existing tests keep passing
      unmodified where behavior is unchanged).
- [ ] The dashboard + Qlippy approve flows and the iPad desk propose flow
      re-walked (the iPad flow on Simulator against a live hub or the seeded
      path).

## Proof required

Migration matrix tests green including the new version hop; zero references
to the sentinel id; both callers' end-to-end tests green with one engine
(diff shows the duplicate logic deleted, not moved); the audit-parity test
(card approve ≡ dashboard approve, Phase 56) still green; full suite green.
