# HS-73-10 — Closeout: the inhabited walk

- **Status:** done
- **Priority:** HIGH (the phase's bar is behavioral; only a walk can prove it)
- **Depends on:** HS-73-01 … HS-73-09
- **Evidence:** [evidence-story-10.md](./evidence-story-10.md)

## Goal

Prove the mission literally: a user runs `holdspeak web`, arrives in the
world at `/`, and **every verb of the daily walk happens inside it, with
zero route changes** except an explicit "Open full". Then re-shoot the
side-by-side against the iPad — judging the *touch*, not the glance (the
honest lesson of Phase 71's vibe test).

## Scope

- **In:** the scripted walk; the route-change assertion; the side-by-side +
  per-verb table; the full verification matrix; `final-summary.md`; the
  owner's cold walk as the acceptance question.
- **Out:** fixing anything non-trivial found here (a real finding reopens
  the owning story; the closeout does not absorb scope).

## Tasks

- [ ] **The walk, as one committed Playwright script** (`tests/e2e/`,
      seeded via real `/api/*` POSTs):
      1. Load `/` (configured profile) — the world, full-bleed, nav hidden
         at idle. (Separately: a fresh profile lands on `/welcome` — the
         guard re-asserted.)
      2. `+ Note` → materialize + NEW beat → type in place → persisted
         (API-verified).
      3. Record orb → start (seeded/real hub recording) → pulse + elapsed
         → stop → the meeting object materializes.
      4. Tap the meeting → pull-out with grouped derivatives → an artifact
         row opens in place → back.
      5. Rail → run an agent → theater → the result lands in-world.
      6. Drag the note onto a zone → the `PUT` fires → tray thumbnails +
         count update → dive → back → Tidy.
      7. **Assert the pathname never left `/`** for steps 1–6; then "Open
         full" on the meeting asserts the ONE sanctioned navigation.
- [ ] Real-metal pass of the same walk by hand on the Mac (real mic for
      the orb, the `.43` endpoint for the agent run), screenshots per
      step — the preferred evidence per the standing real-metal rule.
- [ ] **The side-by-side, re-shot:** the web `/` hero vs the iPad
      `2001-ipad-wide` reference; and the **per-verb table** in the final
      summary — for each verb (arrive, create, edit, open, record, run,
      file, dive), where it happens on each surface. Every web row must
      say "in-world". This table replaces the glance-based vibe test.
- [ ] The matrix, one run, outputs captured: full python suite
      (`--ignore=tests/e2e/test_metal.py`), `cd web && npm run build`,
      route pre-flight (the new route set), the desk unit tests (sprites
      hash parity, wire normalizers), density guard, the HS-73-09 locks,
      voice/doc/mermaid guards.
- [ ] `final-summary.md` per the template; `current-phase-status.md`
      frozen; README "Current phase" + phase index advanced; push + PR +
      merge on green (the standing phase-close cadence).
- [ ] **The owner's cold walk is the acceptance question:** the owner opens
      `/` and runs the daily loop unprompted. The phase's opening quote
      ("a primitive copy, an uninviting mess") is the test — closed only
      when the owner would not say it again, or with the walk explicitly
      listed as the standing follow-up.

## Proof required

The Playwright walk green in CI (committed, not a one-off); the real-metal
screenshot sequence; the per-verb table with every web row in-world; the
side-by-side pair; the matrix outputs; `final-summary.md`; the merged PR;
the owner walk recorded as done or as the standing follow-up.

## Done

Shipped — the phase's exit ritual walked in ONE continuous browser
session on one seeded hub: arrive → create+edit a note → arrange → a zone
arriving in rename → file by drag → dive → open → edit → surface → the
meeting drawer → the artifact stack → back → the rail ask (the REAL .43
model answered "inhabited") → the orb flipping on a real external live
frame and settling. location.pathname asserted `/` after every one of the
8 beats; zero page errors; the final world committed as
10-the-inhabited-desk.png. Phase closed 10/10 with final-summary.md. See
[evidence-story-10.md](./evidence-story-10.md).
