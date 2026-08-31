# HS-158-06 - The close: gates, suite amendments, final summary

- **Project:** holdspeak
- **Phase:** 158
- **Status:** done
- **Depends on:** HS-158-01, HS-158-02, HS-158-03, HS-158-04, HS-158-05
- **Unblocks:** Phase P1a (The Interview)
- **Owner:** unassigned

## Problem

P1 claims the aggregate. The close proves it: full suite CI-style,
name-diff zero branch-new, web gates, counsel, the SRS suite amended
with every P1 discovery (the precedence rule), and the owner's shot
verdict already recorded on 05 before the PR merges.

## Scope

- **In:** full suite isolated HOME `-n auto` (metal excluded);
  name-diff vs main's latest run — zero true branch-new or root-cause
  fixes (load-flakes proven by isolated greens, per the 157
  precedent); `npm --prefix web run check` + baseline; counsel close
  (M in-round); suite amendments (incl. the room-section vocabulary
  in CONTRACTS-P0.md and counsel-157's N-2 Note/artifact row split if
  this phase touches §3.2); restore any suite-regenerated shot PNGs
  in OTHER phases before staging (the 157 scar); roadmap cadence
  files; `final-summary.md`; PR gated on conclusion JSON in its own
  step + name-diff, merged via merge commit AFTER the owner's 05
  verdict.
- **Out:** P1a work.

## Acceptance criteria

- [ ] Full suite run and READ; name-diff zero true branch-new (candidates proven at root cause).
- [ ] Web check green; baseline zero branch-new.
- [ ] Counsel: zero open must-fix; M-findings fixed in-round.
- [ ] Suite amendments committed (or explicit none-arose note); N-2 resolved or explicitly deferred.
- [ ] final-summary.md; phase COMPLETE 6/6; README pointers true; PR merged (conclusion JSON read in its own step; the owner's verdict on 05 recorded first).

## Test plan

- **Everything:** this story IS the gate run.

## Gate record (running)

- **Web gates:** `npm --prefix web run check` GREEN on rerun (exit 0,
  bundle gate passed; first run's sole failure was the known
  ModelLibraryCore radio flake). Baseline: 1862 passed / 1 failed on
  both full runs — but a DIFFERENT untouched-file test each time
  (ThoughtDocumentPane reveal, then NotePullout scroll-reveal), and
  the first run's check-side flake was a third (ModelLibraryCore).
  All three isolated GREEN (9/9, 9/9, 28/28) on files
  `origin/main..HEAD` never touched — load-flake churn, zero true
  branch-new. Proof commands + outputs in the session record.
- **Suite amendment duty:** counsel-157 N-2 RESOLVED — SRS §3.2
  Note/artifact row split into two registered ref types (rides this
  close commit).

## What shipped

- Full suite CI-style: `12 failed, 7968 passed, 54 skipped in 21:47`
  — sweep vs main's fresh baseline (26 names @ 6a5bd3e4): 2
  candidates, both isolated GREEN (0.70s / 10.08s) on untouched
  files. Zero true branch-new.
- Web gates: check exit 0 + bundle gate; baseline's three churn
  flakes proven (see Gate record). 185 suite-regenerated PNGs
  restored to HEAD before staging (the 157 scar).
- Counsel RATIFY-W-C, conditions discharged; suite amendments landed
  (SRS §3.2 split; CONTRACTS-P0 `project` row); final-summary.md
  written; phase COMPLETE 6/6.

## Counsel close (HS-158)

**VERDICT: RATIFY-W-C — zero M, one S, three N.** Conditions
discharged in this commit: (1) S-1 documented below + P2 backlog;
(2) the `project` row added to CONTRACTS-P0's registered type table.

- **S-1 (KNOWN DOM-003 DIVERGENCE → P2):** `add_resource` /
  `remove_resource` / `associate_meeting` / `disassociate_meeting`
  graduate legacy repo calls across THREE transactions (revision
  check+bump / legacy repo's own connection / change+event+command).
  A mid-sequence failure can burn a revision without its change row.
  Acknowledged in code comments; the 8 non-legacy commands (4
  lifecycle + 4 item) are single-transaction correct. FIX AT P2's
  service composition: legacy repo methods accept an external
  connection. 
- **N-1 (P2):** empty-patch `update_project` burns a revision — add
  the `if not fields` guard with P2's command work.
- **N-3 (P2):** field-patch change labels show the `fields` KEY, not
  its values ("Updated · fields") — unfold the array in
  `changeLabel` with P2's Delta/detail work.
- N-2 (CONTRACTS-P0 `project` row) + counsel-157 N-2 (SRS §3.2
  split): both RESOLVED in this phase.

## Notes / open questions

- P1a charters after this merges, anchors re-verified — the standing rule.
