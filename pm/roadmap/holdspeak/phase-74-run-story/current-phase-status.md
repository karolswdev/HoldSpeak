# Phase 74 — The Run Story, Completed

**Status:** open — scaffolded 2026-07-02 (0/5).
**Owner call that opened it:** "Let's keep going" on the recommended
follow-up after Phase 73: complete the desk's run story — the two recorded
hub follow-ups from [phase-73](../phase-73-desk-inhabited/final-summary.md).

## Why

Phase 73 put every desk verb in the world, but a persona/chain/workflow
run is still a dead end: the hub returns output text and forgets it (no
artifact, no lineage, no sync to the iPad), and the run emits no frames
(the GenerationTheater stays dark; the rail fakes nothing and so shows
only its own pulse). The iPad's Track-I artifact review and the desk's
materialize beat are both READY consumers — the hub is the missing half.

## Stories

| ID | Story | Sev | Status | Depends |
|---|---|---|---|---|
| HS-74-01 | Run results persist as artifacts (hub) | HIGH | todo | — |
| HS-74-02 | Run frames: the theater's heartbeat (hub) | MED | todo | — |
| HS-74-03 | The result lands on the desk (web) | HIGH | todo | 01, 02 |
| HS-74-04 | Docs: the run story end to end | MED | todo | 01–03 |
| HS-74-05 | Closeout: the run walk | HIGH | todo | 01–04 |

## Exit criteria

- [ ] A persona/chain/workflow run persists its output as a REAL artifact
      (the one plugin-artifact store; run-born artifacts carry no meeting
      anchor) with capability lineage, and it rides `/api/sync/pull`
      unchanged in shape (HS-74-01).
- [ ] The run routes broadcast honest `intel_status` frames (running →
      ready | error); no fake tokens (HS-74-02).
- [ ] A run from the rail/pull-out materializes the artifact on the desk
      with the NEW beat and `via <capability>` lineage; proven on the
      `.43` endpoint (HS-74-03).
- [ ] Entry-point docs speak the completed loop (HS-74-04).
- [ ] The run walk: ask → theater → the artifact object → open → lineage,
      one session, pathname never leaves `/` (HS-74-05).

## Where we are

**2026-07-02 — scaffolded (0/5).** Seams verified before scaffolding:
`ctx.broadcast` exists on WebContext; the theater consumes
`intel_status {state}` (running reveals, ready settles); artifacts sync
through the plugin-artifact store (`record_artifact` currently REQUIRES a
meeting anchor — 01 loosens it for run-born artifacts only); the desk's
materialize beat (Phase 73's markNew) and the iPad's artifact review are
ready consumers.
