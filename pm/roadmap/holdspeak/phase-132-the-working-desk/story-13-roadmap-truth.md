# HS-132-13 — The roadmap tells the truth

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** none
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Orientation tools report fiction. Verified against git history:

- Five phase headers contradict their own story tables: phase-113 says DRAFT
  with all stories backlog while 23 HS-113 commits shipped stories 01-11;
  phase-114 says DRAFT with six stories "in-progress" and zero HS-114
  commits ever; phase-118 says "backlog (0/10)" with nine stories done;
  phase-121 says "chartered (0/12)" while its kit ships in production;
  phase-124 says "chartered (0/10)" while PR #442 merged it as 10/10.
- Phase 120's entire record (11 done stories) was never committed on any
  branch — it exists only untracked on the owner's disk, with no evidence
  files at all.
- Phases 115, 116, 119 lack `final-summary.md`; phase-101 has an orphaned
  `evidence-story-04.md` (story not done — this one stays untracked by
  standing direction until the owner's sitting).
- `web/test-results/` is untracked noise from a failed Aug-10 Playwright run
  and is not gitignored.

## Scope

### In

- Correct the five phase headers to match their story tables and git
  history; where a story table itself is wrong (113's backlog rows, 114's
  in-progress rows), correct it against the commit record and note the
  correction.
- Land the Phase 120 record through the gate with an honest header note:
  stories done per the shipped commits, evidence files never captured —
  recorded as an evidence debt, not fabricated.
- Write the three missing final summaries from the shipped record (honest,
  short, pointing at the commits/PRs).
- Gitignore `web/test-results/`.
- Re-run `dw check holdspeak` and drive this phase's touched issues to zero
  (the phase-101 sitting-held item is exempt and stays).

### Out

- Rewriting history or manufacturing evidence for work not proven; the
  Phase-114 absorption re-audit (backlog — its findings may all be closed
  elsewhere, but proving that is its own pass).

## Acceptance criteria

- [ ] `dw context holdspeak` reports no issue for phases 113/114/115/116/
  118/119/120/121/124 beyond honestly-recorded evidence debts.
- [ ] Phase 120's record is in git with the evidence-debt note.
- [ ] `.gitignore` covers `web/test-results/`.
- [ ] Every correction cites the commit/PR it was verified against.

## Test plan

- `.githooks/dw check holdspeak` before/after, captured via
  `dw evidence capture`.
