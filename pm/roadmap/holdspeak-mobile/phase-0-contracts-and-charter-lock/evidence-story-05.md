# Evidence — HSM-0-05 — Charter reconciliation & decisions lock

- **Shipped:** 2026-06-18
- **Commit:** Phase-0 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `CHARTER.md` — Quality Gates 3–7 de-flagged: the reconstruction is now the
  owner-confirmed gate list of record (transmission note + Gate-3+ block updated).
- `contracts/SERIALIZATION-CONTRACT.md` — timestamp rule resolved to UTC `Z`
  (§2); the "owner confirm" section records both confirmations as resolved.
- `PROGRAM-RISKS.md` — the program-level risk register (P1–P7) with stop signals,
  spanning the cross-phase risks; the truncated-gate risk recorded as retired.
- `../holdspeak/HANDOVER.md` — one-line discoverability pointer from the desktop
  roadmap to this program.

## Verification artifacts

- **Owner confirmations captured (this conversation, 2026-06-18):**
  - Quality Gates 3–7: "Yeas brother for 1" → confirmed as-reconstructed.
  - Timestamps: "For 2 - we standardize" → standardize on UTC `Z`.
- The UTC-`Z` decision is mechanically enforced: `validate.py` →
  `PASS utc-z: all instants are UTC Z-terminated`.
- Track-F engine remains a Phase-5 measured pick, pre-grounded by the owner's
  inference brief (`research/inference-on-apple.md`).

## Acceptance criteria — re-checked

- [x] Quality Gate list confirmed by the owner; `CHARTER.md` caveats removed.
- [x] Each deferred decision locked or defaulted-with-trigger: gates ✓,
  timestamps ✓ (UTC Z), package home ✓ (HSM-0-03), version scheme ✓ (HSM-0-03),
  Track-F ✓ (Phase-5 measured, pre-grounded).
- [x] The program risk register exists with stop signals — `PROGRAM-RISKS.md`.
- [x] The `holdspeak` roadmap carries a discoverability pointer — `HANDOVER.md`.

## Deviations from plan

The cross-link landed in `holdspeak/HANDOVER.md` (a clean file) rather than the
`holdspeak/README.md` (which had pre-existing uncommitted edits out of this
commit's scope) — same discoverability goal, cleaner blast radius.

## Follow-ups

None — Phase 0 closes with this story.
