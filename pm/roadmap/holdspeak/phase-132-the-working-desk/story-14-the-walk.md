# HS-132-14 — The walk

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** HS-132-03, HS-132-05, HS-132-08, HS-132-09, HS-132-10, HS-132-12
- **Unblocks:** none (exit story)
- **Owner:** unassigned

## Problem

Every UI claim in this phase currently rests on unit tests and code reading:
there is no `playwright.config.*` in the repo, the only browser-walk
artifact is a failed `.last-run.json` with zero traces, and Article IX.2's
screenshot proof is outstanding for the Phase-130 surfaces
(Settings/Models, placement labels, Decision rename — deferred at
`phase-130-one-truth/final-summary.md:58-61`). The audit's two nastiest bugs
(keystroke loss, sticky ALL CLEAR filter) are exactly the class a committed
walk would have caught.

## Scope

### In

- A committed Playwright walk harness (config + `scripts/` entry) against
  the real running hub, 1440 and 393, reusable after this phase.
- The walk covers: live meeting with streaming intel and bookmark
  confirmation (HS-132-03), streaming mic long-capture + named failure
  (HS-132-05, real browser mic), Workbench item typing (HS-132-07),
  Intelligence filter token + Brief triage persistence (HS-132-08), the
  placement dial states (HS-132-10), the write-failure receipts with the hub
  stopped (HS-132-06), plus the Phase-130 IOU surfaces.
- Live `.43` proof: an Ask on `this_machine` and on the LAN destination
  where the receipt, footer, and manifest name the executed model
  (control-vs-treatment per the standing real-metal rule) — the HS-132-09
  honesty proof on real metal.
- Before/after pairs against the audit's findings; error paths are mandatory
  legs (standing rule).
- Full chain captured through `dw evidence capture`; harness checked into
  `scripts/`.

### Out

- Closing by unit tests alone (cannot be waived); mobile-device walks
  (dormant HSM track).

## Acceptance criteria

- [ ] The walk harness runs from a clean checkout against a live hub and is
  committed.
- [ ] Every listed surface walked at both widths with screenshots archived
  in the phase assets; before/after pairs for each repaired defect.
- [ ] The `.43` receipt-honesty proof shows executed model == receipt model
  on both a local and a remote destination.
- [ ] Zero console errors on the walked paths; any finding is fixed or
  ledgered with an owner note before the phase closes.

## Test plan

- The walk itself, captured:
  `.githooks/dw evidence capture holdspeak 132 14 -- <walk command>`.
- Suite state re-confirmed green after any walk-driven fix (quiet tree).
