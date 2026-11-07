# Parked: the system shade's tests

Parked 2026-11-07 with `SystemShade` and `AttentionDrawer` (their code has been
in `web/src/desk/_parked/attention/` since phase 17). No production entry
mounts either one: every importer of the two re-export shims in
`desk/components/` was a test, so the shims are removed and the tests are here.

- Whole files: `gateShade`, `gateShadeCut.a5`, `shadeCoverage`,
  `shadeDoorless202`, `systemShade`.
- Copies of mixed files, as they stood before the shade cases left them:
  `bell.app` (the zone leg and the shade's sections), `needs-you.app` (the cut
  call in the shade), `oneNumberFaces` (the shade's Projects list and its
  Open). The live files keep their other cases.

The `gate:` ref (a held tool call) now opens the Needs you window, where the
held call has Approve and Deny (`web/src/desk/__tests__/gateRefOpen.r1.test.ts`,
`web/src/desk/__tests__/needs-you.app.test.tsx`). Not collected (`_parked`).
