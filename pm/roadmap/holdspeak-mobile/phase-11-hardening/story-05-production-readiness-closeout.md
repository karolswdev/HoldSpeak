# HSM-11-05 — Production-readiness closeout (Gate 7)

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** backlog
- **Depends on:** HSM-11-01, HSM-11-02, HSM-11-03, HSM-11-04
- **Owner:** unassigned

## Problem

The charter's Track L gate (program Gate 7) is production readiness — the
program's final gate. This story is the verdict: run all five scenarios on real
hardware, triage every finding, and declare the runtime ready (or name exactly
what blocks it). Closing this closes the program.

## Scope

- **In:** a production-readiness checklist (the five scenarios pass + every finding
  fixed or filed); a full hardware pass across Tier-1 (iPad Air/Pro M4) and Tier-2
  (iPhone 17 Pro Max); the recorded readiness verdict; the program-level
  `final-summary.md` for this phase and a note on the roadmap README that the
  program reached its terminal gate.
- **Out:** the individual scenario builds (HSM-11-01..04). New features. Shipping
  logistics (TestFlight/App Store) — readiness is declared here; the owner decides
  shipping.

## Acceptance criteria

- [ ] The readiness checklist is written and all five scenarios (HSM-11-01..04 +
      this run) pass on real Tier-1 and Tier-2 hardware, evidenced.
- [ ] Every finding from the scenarios is triaged: fixed, or filed (as a
      `holdspeak-mobile` follow-up or back to the owning phase) with a clear
      blocker/non-blocker call.
- [ ] **Track L gate / Gate 7 — production readiness** is declared with the verdict
      and its evidence recorded; if not ready, the exact blockers are named.
- [ ] The runtime runs all three modes (A fully-local, B hybrid, C endpoint) at
      least once on hardware as part of the readiness pass.

## Test plan

- Manual / device: the full five-scenario pass on Tier-1 + Tier-2 hardware; record
  results + findings + the verdict.
- Unit: the full CI suite green (the accumulated guards from every phase) as the
  fast precondition to the hardware pass.

## Notes / open questions

- This closes Phase 11 and the program; on pass write `evidence-story-05.md` +
  `final-summary.md` and update the roadmap README (program status → shipped /
  ready).
- Readiness is the checklist, not a feeling (phase risk). Fix the definition
  before judging; surface deferred items (encryption-at-rest, background audio) as
  explicit blocker/non-blocker calls.
- "Ready" ≠ "shipped" — the owner owns the App Store/TestFlight decision; this
  gate hands them a runtime that has earned it.
