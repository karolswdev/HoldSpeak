# HS-160-08 - The close: gates, suite amendments, final summary

- **Project:** holdspeak
- **Phase:** 160
- **Status:** done
- **Depends on:** HS-160-01..07
- **Unblocks:** Phase P2a (The GitHub Watch)
- **Owner:** unassigned

## Problem

P2 claims the repeat-use loop. The close proves it: full gates, the
sweep with candidates proven at root cause, counsel (M in-round),
suite amendments, the churn-PNG restore, the final summary carrying
the backlog forward, the PR gated on conclusion + name-diff, merged
on the owner's already-given 06 verdict.

## Scope

- **In:** the standing close liturgy (full suite isolated -n auto;
  name-diff vs main's latest; web check + baseline; counsel;
  amendments incl. any CONTRACTS-P0 additions; PNG restore;
  final-summary.md; PR; conclusion JSON its own step; merge commit).
- **Out:** P2a work.

## Acceptance criteria

- [ ] Full suite run and READ; sweep zero unexplained branch-new.
- [ ] Web check green; baseline zero branch-new.
- [ ] Counsel: zero open must-fix.
- [ ] Amendments committed (or none-arose note); backlog carried in the final summary.
- [ ] final-summary.md; COMPLETE 8/8; README true; PR merged.

## Test plan

- **Everything:** this story IS the gate run.

## Gate record (running)

- **Web gates (final tree):** check exit 0 (guard + bundle gate);
  baseline 2060 passed / 1 failed — the single branch-new is the
  ThoughtDocumentPane Original-disclosure test: the THRICE-proven
  churn flake (158 close, 159 CI, now) — file untouched by
  `origin/main..HEAD`, isolated 1/1 green. Zero true branch-new.
- Sweep baseline fresh: main's 27 names @ run 33459107466.
- Full suite + counsel in flight.

## The CI catch (post-close, pre-merge)

- PR #524's CI found what every local run missed: same-second timing
  puts two observations of ONE fact in one window, both minting the
  SAME deterministic pprop_ id — the id doing its job, the insert
  crashing instead of deduping (UNIQUE failed in open_review; the
  deferred-return test was the messenger, not the cause). FIXED:
  intra-window dedup by deterministic id (one semantic proposal,
  first wins) + the conflict path's `review_window_key=""` "filled
  by caller" placeholder now actually filled (threaded through
  _detect_conflicts). A forced-collision regression test seeds two
  identical facts and asserts ONE proposal. The four other CI
  candidates: churn, proven (untouched files, isolated green ×4).

## Counsel close (HS-160)

**VERDICT: RATIFY-W-C — zero M, four S, five N.** Axes A/D/F clean
(the twelve steps faithful, accept_review genuinely one-transaction,
TST-003 proven, every repo law held). The orchestrator's in-round
ruling on the S-class:

- **S-1 — FIX IN-ROUND (honesty, not debt):** the dismissal basis
  hash uses review_window_key at dismiss and "" at recurrence-check
  — cross-window suppression NEVER fires; everything returns as a
  linked successor. Story 04's flipped acceptance says "DEL-003
  proven: suppresses" — the claim must become true, not backlogged.
  Fix: the observation's source_version at both sites + the test
  asserts TRUE suppression.
- **S-3 — FIX IN-ROUND (trivially cheap):** _store_window writes
  review + N proposals in separate transactions while the
  _in_transaction variants (built in 01 for exactly this) sit
  unused. One conn block.
- **N-3 — FIX IN-ROUND (two lines):** delta.py's captured_at
  default is naive local; becomes aware-UTC.
- **S-2 — PAID by HS-161-07:** decide→create_item split transaction
  joined via create_item_in_transaction (the 159 M-1 conn-threading
  pattern); fault-proven by test_item_insert_fault_rolls_back_decision
  and test_happy_path_single_revision_bump.
- **S-4 — travels with P3 (counsel's condition; owner-approved
  face):** source chips display-only; WEB-DLT-009's open-the-source
  joins the Draft-update story.
- N-1 Space-preview unimplemented (P3), N-2 session-undo is
  UI-local (an undismiss verb is P3+), N-4 sort-field doc note,
  N-5 the no-fetch spy's reach — all recorded.

## What shipped

- Authoritative suite (post-fixes): 12F/8335P in 22:52; sweep vs
  main's 27 → 2 candidates: test_api_surface REAL (the face's
  consumer missing on the review routes — the 159 lesson repeating;
  regenerated, isolated 5-green) and test_one_path_census proven
  churn (mesh_serve.py untouched by the branch; isolated green).
  Zero unexplained branch-new.
- In-round counsel work landed (eca6cde6): S-1 TRUE suppression +
  story-04's record corrected by name; S-3 one-transaction window
  fault-proven; N-3 aware-UTC storage. Backlog carried per counsel's
  conditions (S-2 P2a, S-4/N-1/N-2 P3, N-4/N-5 noted).
- 198 churned PNGs restored; one untracked stray glass PNG PARKED
  (never deleted) to the session scratchpad per the standing rule.
- final-summary.md written; phase COMPLETE 8/8.

## Notes / open questions

- P2a (the GitHub live slice — the stopwatch bar phase) charters after the merge, anchors re-verified. The owner's delivery=GitHub ruling makes it the proving V0 slice.
