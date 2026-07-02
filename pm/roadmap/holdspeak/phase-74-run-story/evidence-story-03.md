# Evidence — HS-74-03 — The result lands on the desk (web)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-74-run-story`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **One store action, `runCapability(kind, id, input)`**: fires the real
  `/run` route; on success with an `artifact_id`, refreshes and marks the
  artifact NEW — the persisted result **materializes on the stage wearing
  the HS-73-06 beat**, exactly the grammar that was "ready when the hub
  persists". Both run surfaces (the rail and the pull-out) now ride it;
  their inline output + Copy behavior is unchanged.
- **The theater plays for free**: the HS-74-02 frames arrive on the one
  runtime bus the shell theater already subscribes to — no client wiring
  was needed, which is itself the proof that the one-bus architecture
  holds.

## Verification artifacts — REAL METAL (the `.43` endpoint)

One Playwright session against the real hub with the real engine:

- Asked from the rail: "Say the word 'landed' and nothing else." → the
  REAL model answered `'landed'` → **the artifact materialized on the
  stage wearing `is-new`**, titled `"Owl: Say the word 'landed' and
  nothing else."` (`03-artifact-landed.png`).
- **The run frames reached the client through the one bus**: a page hook
  on `hs-broadcast` captured exactly `["running", "ready"]` with
  `scope: "run"`.
- Opened the materialized object: the pull-out body IS the model's words,
  and the lineage chip reads **via Owl** (`03-artifact-lineage.png`).
- Zero page errors. vitest 9/9; web build green.
- One locator fix along the way (strict-mode: the rail's result card and
  the pull-out body legitimately hold the same text — scoped selectors).
- Manifest regenerated (guard 5/5); full suite **3080 passed, 37
  skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] A run from either surface materializes the artifact with the beat.
- [x] The frames reach the page through the one bus (asserted, not
      assumed).
- [x] Lineage renders `via <capability>` on the landed object.
- [x] Proven on the `.43` endpoint with an instruction-following check
      (the Phase-53 lesson).

## Deviations from plan

- The mid-run theater screenshot was dropped: the real run completes in
  ~1s and the frame capture asserts the same truth deterministically
  (the theater consumes exactly these frames — its own behavior is
  Phase-69 tested).

## Follow-ups

- HS-74-04 (docs) + HS-74-05 (the run walk closeout).
