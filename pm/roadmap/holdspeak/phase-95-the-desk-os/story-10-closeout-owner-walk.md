# HS-95-10 — Closeout: performance proof, screenshot walk, owner walk

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-01, HS-95-09
- **Unblocks:** phase close

## Problem

This phase was born from a live owner sitting that found the desk clunky
and fragmented. It can only close the same way it opened: the owner at the
desk, on the production build, judging feel — backed by machine proof that
the engine hits its budget and that no journey leaves the world. Phase 93's
lesson is standing law: a code-reviewed UI is not a proven UI; the
screenshot walk and the owner's eyes come before any done-claim.

## Scope

- In:
  - the performance proof: the HS-95-01 CDP frame-timing storm re-run on
    the final assembled build (stage + windows + dock + heaviest core
    open), budgets met with numbers stated;
  - the production screenshot walk: a Playwright drive of the full Desk OS
    against the real hub at 1440 and 393 — arrival, every window opened via
    its real entry point, dock states, snap, minimize/restore, reload
    persistence, every demoted route — zero failed API responses, shots
    archived;
  - the no-exit audit: the HS-95-08 guard plus a recorded interaction sweep
    showing no product-route navigation events from desk interactions;
  - the UAT rider: a Desk OS campaign (or Campaign 1 revision) authored in
    `uat/` so the rig that produced the opening verdict can measure the
    closing one;
  - the owner walk: a live sitting on the production bundle — dictate,
    record and review a meeting, change a setting, edit a workflow, steer a
    session, all through the desk; the owner's verdict recorded verbatim;
  - final-summary.md with honest deferals: anything descoped goes to
    BACKLOG by name.
- Out:
  - fixing findings beyond walk-blocking defects (new findings triage to
    BACKLOG per the standing ritual);
  - native/physical-device legs (candidate Y's program).

## Acceptance criteria

- [ ] Frame budget met on the assembled build: median ≤ 16.7ms, p95 ≤ 33ms
      through the storm scenario, numbers recorded in evidence.
- [ ] The screenshot walk passes at both viewports with zero failed API
      responses; the archive lands with the evidence.
- [ ] The no-exit audit is clean: guard green, zero desk-initiated
      product-route navigations in the recorded sweep.
- [ ] The UAT campaign for the Desk OS exists and runs on the rig
      (conductor stages it; a full pass is executable end to end).
- [ ] The owner completed the walk on the production bundle and the verdict
      is recorded; walk-blocking defects fixed and re-walked, or the phase
      does not close.
- [ ] Full suite green (standing exclusions honored) and the final summary
      names every deferral with its BACKLOG destination.

## Test plan

- `uv run pytest -q` (with the standing metal-test exclusion) — suite
  output read before any flip.
- `npm --prefix web test` — full web suite.
- The Playwright walk script (archived with the evidence, rerunnable).
- The live owner sitting through the UAT conductor.

## Implementation direction

- Assemble the walk script from the per-story Playwright walks; one
  entry-point-driven script, not a route list — the walk must travel the
  way a user does.
- Run the storm with the meeting review window open on a real seeded
  history; an empty desk flatters the renderer.
- Stage the UAT campaign with the existing recipe/deck vocabulary; no new
  conductor machinery unless a beat is impossible without it.
- The owner's words go in the evidence unedited — that is the bar the
  phase answers to.

## Evidence required

- frame-timing capture with stated percentiles;
- the screenshot-walk archive and its zero-failure API log;
- the no-exit sweep recording;
- the UAT campaign files and a staged-run receipt;
- the owner walk verdict, verbatim;
- the full-suite and web-suite outputs.
