# HS-38-06 — Closeout + final-summary

- **Project:** holdspeak
- **Phase:** 38
- **Status:** not-started
- **Depends on:** HS-38-01, HS-38-02, HS-38-03, HS-38-04, HS-38-05
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Close Phase 38 cleanly: prove the safety invariant **still** holds now that actuators
reach real external systems and approve live — every write path is manifest-gated +
permission-gated + still approval-gated + audited — capture the demo, and write the record.

## Scope

- **In:**
  - **Egress-posture review, extended to the write paths:** walk each connector (GitHub,
    webhook) + the live surface and confirm none egresses without (a) an `approved`
    proposal, (b) the policy gate, (c) payload parity, (d) the connector's permission
    manifest + `PermissionGate`, and (e) an audit row. A short written audit in
    `final-summary.md` (the headline).
  - Verify the HS-38-05 docs are present + accurate (drift-guard + link-check green).
  - Final `cd web && npm run build`; confirm `holdspeak/static/_built/` is **not** committed.
  - Capture a **demo** (the live pending-actions panel + an executed write proposal with its
    audit trail) in `evidence/`.
  - `uv run pytest -q --ignore=tests/e2e/test_metal.py` green; routing invariants green
    (actuators still off + unregistered by default); the default suite makes **no real
    outbound call**.
  - `final-summary.md`; flip the project README phase row → `done` + Current-phase +
    Last-updated; refresh `HANDOVER.md` (next frontier after Actuators II).
- **Out:** new work; verification + record.

## Acceptance criteria

- [ ] Egress-posture review written: no write path egresses without approval + policy +
      parity + manifest/gate + audit; the negatives (refused op / off-list host / no
      approval ⇒ no egress) cited.
- [ ] HS-38-05 docs verified; doc drift-guard + link-check green.
- [ ] Demo (live panel + executed write proposal + audit) committed to `evidence/`.
- [ ] Bundle rebuilt (gitignored — not committed); full suite green; routing tests green;
      no real outbound call in CI.
- [ ] `final-summary.md` written; README phase row `done`; HANDOVER refreshed.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- The opt-in connector/live tests re-run for the demo capture (injected runners/clients).
- Doc drift-guard + live-doc link-check green.

## Notes / open questions

- Lead `final-summary.md` with the extended egress-posture review (the reason the phase is
  trustworthy), then the what-shipped table — mirroring Phases 36/37.
- Tee up the next frontier in HANDOVER (e.g. more connectors as packs, an approval inbox
  across meetings, per-role governance) without committing to it.
