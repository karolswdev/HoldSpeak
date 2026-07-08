# HS-86-05 — The live walk + docs + closeout

- **Project:** holdspeak
- **Phase:** 86
- **Status:** done
- **Depends on:** HS-86-04
- **Unblocks:** B2 (the nod — a future phase)
- **Owner:** unassigned

## Problem

The RFC's B1 exit is not "the page renders": it is *"a live walk
where a real story moves station-to-station during a real shipping
commit, with zero belt-side writes."* The story that closes the phase
is itself the object on the belt — the recursion is the proof.

## Scope

- In: the walk — with the hub live and `/belt` open: flip THIS story
  in-progress (`dw story status`), watch the chip move; capture
  evidence (`dw evidence capture`), watch the station; stage a
  deliberately failing contract, watch the gate refusal chip wear its
  rule; land the real commit through the gate, push, watch PR +
  check lights, merge on green, watch the close station — each beat
  screenshot-captured with zero belt-side writes (server logs show
  only GETs on `/api/belt`). Docs: the Belt section in
  `docs/USER_GUIDE.md` (or the Studio doc the IA owns) in canon
  voice + egress badge rules; `docs/ARCHITECTURE.md` gains the belt
  read path; BACKLOG row U → shipped(B1); roadmap README cadence;
  final-summary + this phase's closeout.
- Out: announcing/publishing; B2 scoping beyond the final summary's
  handoff notes.

## Acceptance criteria

- [ ] The walk's beat-by-beat captures exist in evidence and every
      state shown is derivable from receipts recorded in the same
      evidence (no staged screenshots).
- [ ] Hub access log excerpt in evidence: only GET under `/api/belt`
      for the whole walk.
- [ ] Docs updated in canon voice; voice/docs guards green; BACKLOG
      row U and the roadmap README updated in the same commit as the
      closeout per the operating cadence.
- [ ] `final-summary.md` written; full suite green; PR merged on
      green CI.

## Test plan

- Unit: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Integration / Cypress: the live walk itself (captured).
- Manual / device: the owner replays the walk from the docs alone.

## Notes / open questions

- The gate-refusal beat uses a REAL refusal (an honest unchecked
  contract) — staged dishonesty to produce a screenshot would violate
  the phase's own thesis.
