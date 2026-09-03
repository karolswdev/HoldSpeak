# HS-166-05 - The live walk: real acli, real site(s) — OWNER VERDICT

- **Project:** holdspeak
- **Phase:** 166
- **Status:** done
- **Depends on:** HS-166-03, HS-166-04
- **Unblocks:** HS-166-07
- **Owner:** unassigned

## Problem

The exit is LIVE or nothing: "Jira readiness is backed by live
discovery/search and the same no-duplicate Delta/action behavior,
never pushed fixtures alone" (§14 P7; V0-D: "MUST NOT simulate
readiness with pushed fixtures"). SETFLOW-005: a blocked/due-risk
Watch produces one typed Delta and one configured action after a
transition, with no duplicate on unchanged refresh.

## Scope

- **In:** the owner's real acli with his real account(s) — TWO
  connections if he has them (the multi-target focus: two sites, or
  two accounts), else one plus the honest note. The wrapper BUILDS
  FIRST, then drives: connections listed + rechecked (switch/read-
  back visible in the transcript) → discover projects/types/
  statuses on each → the interview proposes `watch.jira.blockers`
  or `.due_risk` → clarify scope → test (population shown) →
  finalize (baseline, no false transitions) → the owner (or the
  wrapper via `acli jira workitem transition`, declared as HARNESS
  action, never a product effect) moves one issue into the blocked
  state → evaluate → ONE `jira.issue.status_changed` → ONE Delta →
  ONE door item (receipted) → refresh unchanged → no_op, zero
  duplicates → Web and MCP read the same revisions. Every number
  measured into the transcript; the gallery republished (the 165
  precedent: a wire transcript is a face). Every recorded fixture
  from 01-03 is RE-RECORDED against the real CLI here; a mismatch
  fixes the adapter.
- **Out:** docs (06), the close (07).

## Acceptance criteria

- [x] Live discovery/search on ≥1 real `*.atlassian.net` site through acli (no fixture in the path — asserted by the wrapper's runner audit).
- [x] One transition → one typed Delta + one action; unchanged refresh → zero duplicates; x2 deterministic on the same window.
- [x] The owner's verdict recorded VERBATIM; a bounce is a finding, fixed at the root.

## Test plan

- **Live:** the walk wrapper (story166-05-verify.sh) under dw capture; transcript + shots in assets/.

## Trace record (orchestrator round, 2026-09-03)

- THE EXIT, MEASURED LIVE (the owner's real acli 1.3.36, OAuth,
  karolsaneapple.atlassian.net, project KAN, x2 at 1440 + 393,
  counts_match true; every number from the wire/DB):
  tick 1 (after finalize) → 1 evaluation, 0 transitions, 0 effects,
  0 runs, 0 door items; ONE declared harness transition (KAN-1
  In Progress → Done, reverted in a finally) → tick 2 → 3 transitions
  (status_changed + category_changed + resolved), 2 effects
  (observe + steward.run_once), 1 steward run completed, ONE door
  item "[Steward] KAN-1 In progress → Done"; the Delta review: 5
  proposals with jira evidence; tick 3 unchanged → 0/0/0; the run
  replayed with its watermark → the same run id; Web ↔ MCP parity
  (room revision, watch state, delta review id, door count) true via
  in-process dispatch (the stdio transport was proven in 165). The
  real DB untouched (guarded). Accounts covered: 1 (the owner holds
  one; the second-target proof is ledgered, never faked).
- FOUR PRODUCT DEFECTS the walk forced into the open and paid, each
  with unit tests (tests/unit/test_hs166_walk_fixes.py, 13):
  (1) FALSE BASELINE — finalize wrote baseline_state=established
  with no snapshot; the first unattended tick "discovered"
  everything and fired effects + a run from nothing (provider-
  agnostic; 164 counted that tick as a useful run). Finalize now
  calls baseline_watch per activated watch; a failed fetch leaves
  `pending`, never a dressed-up baseline. (2) NO DOOR ITEM from a
  jira transition — two breaks: the web context composed the Delta
  service WITHOUT project_service, so decide_proposal's create_item
  silently skipped (an `if None` on a new path; also GitHub's);
  and watch transitions only ever produced record-only
  observation_attention. Now `attach_project_service()` (public,
  documented mutual composition) and a risk rule keyed on the
  WATCH'S OWN matched conditions through the one matcher
  (due_within → medium, overdue/blocked → high) → risk_attention →
  a dependency item at_risk → the door candidate; pure discovery
  transitions never promote. (3) REPLAY minted a new run — the
  route had no watermark gate; `find_run_by_watermark` is now ONE
  service helper used by the drain's Gate 4 and the route. (4) The
  door title was a wire id ("risk_attention: wat…") → built from
  the entity key + status NAMES (category keys mapped to labels).
- Also learned: Jira Cloud search is eventually consistent (~3-6 s
  after a transition; the walk polls); acli cannot set due dates;
  the observation's source id is the project_sources binding
  (psrc_), not the watch id — resolved in the rule.
- The face on the real account: accounts (the owner's card
  CONNECTED), scope (real KAN / SAM1), population, preview (real
  issues + due dates), the ProgressPlan test (1 found, 2 calls),
  review, the Room, the Door with the item, the Delta — at both
  widths. Three face defects it exposed (date-only due dates
  rendering a day early; "DUE AT DUE WITHIN DAYS 7"; "EVERY 1440
  MIN") fixed in-round on the face and re-walked.
