# HS-73-09 — Closeout: the inhabited walk

- **Status:** todo
- **Priority:** HIGH (the phase's bar is behavioral; only a walk can prove it)
- **Depends on:** HS-73-01 … HS-73-08

## Goal

Prove the mission statement literally: **every verb of the daily walk
happens inside the world, with zero route changes** except an explicit
"Open full". Then re-shoot the side-by-side against the iPad — this time
judging the *touch*, not the glance (the honest lesson of Phase 71's vibe
test).

## Scope

- **In:** the scripted walk; the route-change assertion; the side-by-side;
  the full verification matrix; `final-summary.md`.
- **Out:** fixing anything non-trivial found here (a real finding reopens
  the owning story; the closeout does not absorb scope).

## Tasks

- [ ] **The walk, as one committed Playwright script**
      (`tests/e2e/` beside the route pre-flight, seeded via real `/api/*`
      POSTs the way HS-71-03 seeded):
      1. Load `/desk` — full-bleed, nav hidden at idle.
      2. `+ Note` → object materializes → type in place → content persists
         (API-verified).
      3. Record orb → start (seeded/real hub recording) → pulse + elapsed →
         stop → the meeting object materializes with the NEW beat.
      4. Tap the meeting → pull-out with grouped derivatives → tap an
         artifact row → opens in place → back.
      5. Rail → run an agent → theater → the result lands in-world.
      6. Drag the note onto a zone → the `PUT` fires → tray thumbnail +
         count update → dive in → back → Tidy.
      7. **Assert `location.pathname === "/desk"`** (under the `/_built`
         base) **for the entire walk**; then "Open full" on the meeting →
         asserts the ONE sanctioned navigation.
- [ ] Real-metal pass of the same walk by hand on the Mac (real mic for
      the orb, the `.43` endpoint for the agent run), screenshots captured
      per step — the preferred evidence per the standing real-metal rule.
- [ ] **The side-by-side, re-shot:** the web desk hero + the iPad
      `2001-ipad-wide` reference; and a *verb table* in the final summary —
      for each verb (create, edit, open, record, run, file, dive), where it
      happens on each surface. Every web row must say "in-world". This
      table is the phase's honest replacement for the glance-based vibe
      test.
- [ ] The matrix, one run, outputs captured: full python suite
      (`--ignore=tests/e2e/test_metal.py`), `cd web && npm run build`,
      route pre-flight, density guard (the new desk caps), the HS-73-08
      locks, voice/doc guards.
- [ ] `final-summary.md` per the template; `current-phase-status.md`
      frozen; README "Current phase" + phase index advanced; push + PR +
      merge on green (the standing phase-close cadence).
- [ ] Flag the owner walk: the owner opens `/desk` cold and runs the daily
      loop unprompted. The phase's opening quote ("a primitive copy, an
      uninviting mess") is the acceptance question — closed only when the
      owner would not say it again.

## Proof required

The Playwright walk green in CI (committed, not a one-off); the real-metal
screenshot sequence; the verb table with every web row in-world; the
side-by-side pair; the full matrix outputs; `final-summary.md`; the merged
PR. The owner's cold walk recorded as done or explicitly listed as the
standing follow-up.
