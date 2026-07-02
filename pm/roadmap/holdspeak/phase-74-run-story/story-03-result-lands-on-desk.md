# HS-74-03 — The result lands on the desk (web)

- **Status:** todo
- **Severity:** HIGH
- **Depends on:** HS-74-01, HS-74-02

## What

A run fired from the rail or the pull-out ends with the artifact
MATERIALIZING on the stage (the Phase-73 beat): refresh + markNew(the
response's artifact_id). The result card keeps the inline output + Copy
(nothing regresses) and the new object opens to `via <capability>`
lineage. The theater plays during the run (the HS-74-02 frames) — the
Phase-73 "honest finding" is closed for real.

## Test plan

- Playwright (stub engine): rail run → the artifact object appears
  wearing is-new; its pull-out shows the body + `via` lineage chip.
- REAL METAL (the `.43` endpoint): the same ritual with a real model
  answer landing as the artifact's body; the client received the
  intel_status frames (asserted via a page hook).
