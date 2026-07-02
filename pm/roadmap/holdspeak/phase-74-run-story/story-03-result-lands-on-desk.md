# HS-74-03 — The result lands on the desk (web)

- **Status:** done
- **Severity:** HIGH
- **Depends on:** HS-74-01, HS-74-02
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

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

## Done

Shipped. One store action (runCapability) fires the real route and, on an
artifact_id, refreshes + marks NEW — the persisted result materializes on
the stage wearing the HS-73-06 beat; both run surfaces ride it with their
inline output + Copy unchanged. The theater plays with ZERO client wiring
(the frames arrive on the one bus it already speaks — the architecture
holding is the proof). REAL METAL: the .43 model's 'landed' answer
materialized as "Owl: Say the word 'landed'…", the page hook captured
exactly [running, ready] with scope run, and the opened object shows the
model's words with via-Owl lineage; two screenshots; zero page errors.
See [evidence-story-03.md](./evidence-story-03.md).
