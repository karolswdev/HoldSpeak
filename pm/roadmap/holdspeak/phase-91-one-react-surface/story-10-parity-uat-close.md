# HS-91-10 — DeskOS parity walk, UAT, docs, and close

- **Project:** holdspeak
- **Phase:** 91
- **Status:** in-progress
- **Depends on:** HS-91-09
- **Unblocks:** none
- **Owner:** unassigned

## Problem

A framework migration can be technically complete while the product still
feels inconsistent or loses the native product's character. The phase closes
only on real owner workflows, visual comparison with actual Swift DeskOS, and
an evidence-backed capability walk.

## Scope

- In: full visual/accessibility audit; actual Swift-vs-Web parity captures;
  owner UAT campaign; performance/bundle review; defect sweep; architecture,
  contributor and user-doc updates; final migration census and phase close.
- Out: claiming responsive Web validates iPad/iOS; unrelated feature work;
  deferring framework residue after declaring the phase closed.

## Acceptance criteria

- [x] Desktop and compact-Web audit is clean across all canonical routes: 200,
      zero console errors, unnamed controls, native fallbacks, sub-24 px targets
      and horizontal overflow.
- [ ] Actual Swift DeskOS and Web captures cover arrival, Desk, Dictation,
      Meetings, Settings and Studio; hierarchy, material, spacing, type, motion,
      controls, trust signals and empty/error states are reviewed explicitly.
- [ ] Owner UAT completes at least one real first-run/model setup, dictation,
      live meeting→archive, Desk create/edit/ask, profile change, and Workbench
      interaction; failures are fixed or remain open with phase status not done.
- [x] Performance budgets are recorded for initial shell and heavy routes;
      route-level lazy loading prevents History/Live/Workbench from bloating the
      arrival bundle.
- [x] Full tests/build/guards pass, docs state one React frontend, and the phase
      exit census proves zero Astro/Alpine residue.

## Test plan

- Unit: full React suite and typecheck.
- Integration: full relevant pytest, audit script and UAT conductor campaign.
- Manual / device: actual macOS Swift DeskOS plus hosted Web; compact-Web tested
  only as responsive Web; native iPad/iPhone follows its separate protocol.

## Notes / open questions

This story cannot waive a failed owner workflow in order to close the phase.
Material parity allows intentional platform differences, but each difference
must be named and justified in evidence.
