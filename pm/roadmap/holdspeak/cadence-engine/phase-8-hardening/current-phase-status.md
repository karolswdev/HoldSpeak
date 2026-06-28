# Cadence Phase 8 — Hardening + dogfood (the finale)

**Status:** done — **the Cadence Engine program is COMPLETE (8/8).** **Start here:** `../README.md`.

**Last updated:** 2026-06-28 (Phase 8 shipped: the telemetry-free audit export, the end-to-end flow
test, the master off-switch proof, the user doc, and the dogfood section. Program closed.)

## Objective

Make the engine trustworthy enough to run daily, and prove the whole thing end to end.

## What shipped

- **Telemetry-free local audit** (`cadence/audit.py` `export_audit`): a complete local snapshot of
  every loop, its evidence, the nudge history, and policies, with an honest `egress: local` badge.
  `holdspeak cadence audit [--out FILE]` + `GET /api/cadence/audit`. Pure read, nothing leaves the
  machine.
- **End-to-end flow test** (`tests/integration/test_cadence_e2e.py`): the full chief-of-staff journey
  in one test (project → brief → end-of-day review → apply a decision → audit), plus the audit is
  local + JSON-serializable, plus the **master off-switch** proof (disabled ⇒ the runtime starts no
  cadence thread; run-now/audit still work on demand).
- **The user doc** `docs/CADENCE.md` (linked from `docs/README.md`): the shape, the surfaces, how to
  turn it on, and the trust boundary in product-tense.
- **The dogfood protocol** gained a *Tier C — the Cadence Engine* section (projection, brief +
  review, decisions-stick, no-egress audit, the master off-switch, the optional agent-blocker walk).

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-8-01 | Telemetry-free local audit export (`export_audit`) + CLI + route | done |
| CAD-8-02 | End-to-end flow test (project → brief → review → apply → audit) | done |
| CAD-8-03 | Master off-switch proven end-to-end | done |
| CAD-8-04 | `docs/CADENCE.md` + the `docs/README.md` pointer | done |
| CAD-8-05 | The dogfood protocol Tier-C cadence section | done |

## Exit criteria

- The audit export is local + complete; the e2e flow passes; the off-switch is proven; the doc + the
  dogfood section ship. `uv run pytest -q` green (205 cadence/web/doc-guard tests).
- **The program is closed.** All 8 phases done; the live `.43` LLM proof recorded
  (`../phase-7-llm-nba/proof/real-metal-43.md`). The remaining owner button is the live dogfood walk
  (and turning the master switch on).
