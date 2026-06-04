# HS-37-07 — Closeout + final-summary

- **Project:** holdspeak
- **Phase:** 37
- **Status:** not-started
- **Depends on:** HS-37-01, HS-37-02, HS-37-03, HS-37-04, HS-37-05, HS-37-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Close Phase 37 cleanly: prove the safety invariant holds end-to-end (no external side
effect without an explicit, audited, per-action approval; executed == previewed), capture
the demo, and write the record. (The actuator documentation is its own story — HS-37-06.)

## Scope

- **In:**
  - **Egress-posture review:** walk every actuator path and confirm none egresses without
    (a) an `approved` proposal, (b) payload parity, and (c) an audit entry — a short
    written audit in `final-summary.md` (the phase's headline argument).
  - **Verify the docs** shipped by HS-37-06 are accurate + green (drift-guard +
    link-check) — the authoring/README/doc-truth update itself is HS-37-06's deliverable,
    not the closeout's.
  - Final `cd web && npm run build`; confirm `holdspeak/static/_built/` is **not**
    staged/committed (gitignored build product).
  - Capture an **e2e demo** screenshot of the approval surface + an executed/audited
    proposal in `evidence/`.
  - `uv run pytest -q --ignore=tests/e2e/test_metal.py` green; routing tests green
    (actuators additive + gated).
  - `final-summary.md`; flip the project README phase row → `done` + Current-phase +
    Last-updated; refresh `HANDOVER.md` (what's the next frontier after actuators).
- **Out:** new work; this is verification + record.

## Acceptance criteria

- [ ] Egress-posture review written: no path egresses without approval + parity + audit;
      the negative test (no approval ⇒ no action) is cited.
- [ ] The HS-37-06 docs are verified present + accurate; doc drift-guard + link-check green.
- [ ] e2e demo screenshot committed to `evidence/`.
- [ ] Bundle rebuilt (gitignored — not committed); full suite green; routing tests green.
- [ ] `final-summary.md` written; README phase row `done`; HANDOVER refreshed.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Opt-in reference-actuator e2e (HS-37-05) re-run for the demo capture.
- Doc drift-guard + live-doc link-check green.

## Notes / open questions

- Lead the `final-summary.md` with the **safety invariant** (the reason actuators are a
  whole phase), then the what-shipped table — mirroring the Phase 36 closeout format.
- Tee up the next frontier in HANDOVER (e.g. multi-step action chains, an actuator pack,
  or per-role governance) without committing to it.
