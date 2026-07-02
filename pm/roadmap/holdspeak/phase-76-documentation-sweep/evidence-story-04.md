# Evidence — HS-76-04 — WEB_DESK.md: the flagship documented

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-76-documentation-sweep`)

## What changed

A full rewrite — the audited doc described a pre-73 world (the Desk "at
/desk, in the Studio tier", "Tidy in the header", no orb/rail/chips). The
new doc documents the shipped flagship, every claim traceable to code:

- The front door at `/` with the first-run guard behavior; `/desk`
  redirects home.
- The object vocabulary (incl. artifacts with lineage — new since the
  old doc).
- The chrome (the menu, the hub dot, the egress badge as the one trust
  answer, the create chips, the conditional Tidy, the orb, the rail).
- The verbs, each in label voice: create-in-place (no dialog windows),
  open-in-place (the panel, the artifact stack, Open full as the one
  navigation), file/dive/rename, record from the orb (the hub recorder,
  never the browser mic; "live elsewhere"; the landing meeting), ask
  from the rail (the persisted artifact with lineage), the preview card,
  arrange/Tidy, Qlippy.
- The real-hub screenshot at the top.

## Verification artifacts

- Doc guards: **85 passed, 2 skipped** on the rewrite.
- Every behavioral claim in the rewrite was shipped and proven in the
  Phase 73–75 evidence chain (the doc introduces no claim those proofs
  did not cover).

## Acceptance criteria — re-checked

- [x] The flagship has a truthful doc of its own, verb by verb, linked
      from README (HS-76-02's row) and the entry points.
