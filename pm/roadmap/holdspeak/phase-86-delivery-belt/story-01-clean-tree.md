# HS-86-01 — The clean tree: fix the 31 triaged desyncs

- **Project:** holdspeak
- **Phase:** 86
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-86-02
- **Owner:** unassigned

## Problem

The upstream flagship dogfood (delivery-workbench phase 16,
evidence-story-04) triaged this repo's roadmap to 31 real desyncs the
belt would otherwise wear forever: 12 holdspeak + 2 mobile phases
whose stories are all done but no `final-summary.md` exists,
`phase-15-out-and-about` with no status doc, genuine header↔table
status drifts (mostly the mobile roadmap), three dash story links in
phase 24, one malformed link (HSM-14-06), one premature evidence
(phase 13), one unreadable stray under `docs/evidence/`. The belt
renders receipts; first make the receipts tell the truth.

## Scope

- In: retrospective final summaries for the summary-less done phases
  — each opening with the line "Retrospective closeout (2026-07-07),
  reconstructed from evidence files + git history", content limited
  to what the evidence trail supports; a minimal honest
  `current-phase-status.md` for phase 15 (not-started, no invented
  stories); header↔table drift fixes where the TABLE carries the
  richer truth (headers updated to a recognized token + the table's
  parenthetical truth preserved); phase-24 story-file stubs for
  HS-24-03/04/05 (backlog, from the phase doc's own descriptions) or
  dash-row repair; the HSM-14-06 link fix; the phase-13 evidence/
  status reconciliation; the unreadable stray repaired or retired.
- Out: closing phases 24/25 (hardware-gated, genuinely open);
  changing any evidence file's content; touching upstream dw.

## Acceptance criteria

- [ ] `~/dev/reusable-processes/pmo-roadmap/bin/dw --root . check`
      exits 0 with zero ERROR lines across both projects.
- [ ] Every new final summary carries the retrospective-closeout
      label and links only artifacts that exist.
- [ ] `dw state` still reports current phase 85/closed (86 once the
      README pointer moves) and phase story counts unchanged except
      where a fix corrected them.
- [ ] Full HoldSpeak suite green (docs-only change; the doc-drift
      guards are the relevant tests).

## Test plan

- Unit: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Integration / Cypress: the `dw check` run captured in evidence.
- Manual / device: n/a.

## Notes / open questions

- Retro summaries are receipts of a closure DECISION made now, about
  work evidenced then — the label keeps that honest.
