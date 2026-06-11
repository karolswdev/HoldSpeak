# HS-56-07 — Closeout: live dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 56
- **Status:** backlog
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
- [ ] Dogfood transcript + screenshots committed covering dock, actuator
      card (with the audit-parity proof), learned card, aftercare card, the
      queue, and the off-proof.
- [ ] Full suite green; build clean; 0 `_built/` tracked.
- [ ] `final-summary.md` ships in the same commit as this story's done-flip.
- [ ] README + BACKLOG (J shipped, G absorbed) updated in the same commit.
- [ ] PR to `main` merged on green CI.

## Test plan
- The dogfood above + the full suite; CI green on the PR.

## Notes / open questions
- Dogfood scripts write per-story screenshot names; never overwrite committed
  evidence (the Phase-54 lesson).
