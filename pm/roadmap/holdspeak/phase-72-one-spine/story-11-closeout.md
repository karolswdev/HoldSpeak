# HS-72-11 — Closeout: the one-spine proof

- **Status:** todo
- **Priority:** HIGH (a cohesion phase that is not proven whole shipped nothing)
- **Depends on:** HS-72-01 … HS-72-10

## Goal

Prove the spine holds as one system, not as ten green stories. The closeout
runs every guard this phase built, walks the cross-surface path end to end,
and writes the final summary.

## Scope

- **In:** the full verification matrix in one run; the cross-surface walk;
  the drift-guard spot-check; `final-summary.md`; the phase index + README
  pointer advanced; the owner-walk flag.
- **Out:** fixing anything non-trivial found here (a real finding reopens
  the owning story — the closeout does not absorb scope).

## Tasks

- [ ] The matrix, one run, outputs captured: full python suite
      (`--ignore=tests/e2e/test_metal.py`), web `npm run build` + route
      pre-flight, `swift test` + full `xcodebuild` (Simulator), the
      tri-surface contract validation (HS-72-01), the API-manifest snapshot
      (HS-72-02), voice/doc/mermaid/density guards.
- [ ] The cross-surface walk, captured: create a note on the web `/desk` →
      hub persists → sync pull validates against the schemas → the note
      opens on the iPad Simulator desk → edit there → sync push → the edit
      shows on web. Then the coder path: iPad coder board (renamed routes) →
      select → remote dictation lands in a live session.
- [ ] Drift-guard spot-check: one deliberate schema drift + one unregistered
      route in a scratch commit; both guards fail; revert (captured).
- [ ] `final-summary.md` per the template; `current-phase-status.md` frozen;
      README "Current phase" + phase index row updated; push + PR + merge on
      green (the standing phase-close cadence).
- [ ] Flag the owner device walk (the iPad half of the cross-surface walk on
      real metal) — Simulator evidence is recorded as the floor; the phase
      may close on it only with the walk explicitly listed as the standing
      follow-up, per the verify-on-device rule.

## Proof required

Every matrix output pasted or linked in the evidence file; the walk
screenshots (web desk, Simulator desk, the landed dictation); the two red
drift-guard captures; `final-summary.md` written; PR merged on green.
