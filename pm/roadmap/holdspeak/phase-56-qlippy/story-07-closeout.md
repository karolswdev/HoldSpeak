# HS-56-07 — Closeout: live dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** HS-56-01..06
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
The phase's claims are behavioral (reflects, offers, never acts, never steals
focus, byte-identical off) — only a live runtime proves them.

## Scope
- **In:**
  - **Dogfood (live runtime, mascot on):** the dock follows real runtime
    states; a real actuator proposal slides the alert card out with the
    three privacy answers; **Approve on the card produces the identical
    audited transition a dashboard approval does** (shown side-by-side or by
    audit trail); a real journal correction with reach fires the learned
    card; a wrapped meeting with open items fires the aftercare card; the
    queue holds when two events race. Screenshots throughout.
  - **The off-proof:** mascot off → the presence page output byte-identical;
    presence off → nothing.
  - Full suite green; `npm run build` clean; 0 `_built/` tracked.
  - `final-summary.md`; phase CLOSED here + project README; BACKLOG **J**
    flipped to shipped and **G** marked absorbed-shipped.
  - Push `phase-56-qlippy`, PR to `main`, merge on green CI.
- **Out:** new feature work (findings go back to their story first).

## Acceptance criteria
- [x] Dogfood transcript + screenshots committed covering dock (driven over
      the REAL socket, not DOM events), actuator card (audit parity shown
      side by side: card approve == dashboard approve, both
      `approved`/`web-user`), learned card (honest reach), aftercare card,
      the queue holding a race ("+1" on the sticky card), and the off-proof
      (byte-identical page + no card on either flag) — 9/9, zero page
      errors, five screenshots (see `final-summary.md`).
- [x] Full suite green (2602 passed, 17 skipped); build clean; 0 `_built/`
      tracked.
- [x] `final-summary.md` ships in the same commit as this story's done-flip.
- [x] README + BACKLOG (J shipped, G absorbed-shipped) updated in the same
      commit.
- [x] PR to `main` merged on green CI.

## Test plan
- The dogfood above + the full suite; CI green on the PR.

## Notes / open questions
- Dogfood scripts write per-story screenshot names; never overwrite committed
  evidence (the Phase-54 lesson).
