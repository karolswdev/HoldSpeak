# HS-166-05 - The live walk: real acli, real site(s) — OWNER VERDICT

- **Project:** holdspeak
- **Phase:** 166
- **Status:** backlog
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

- [ ] Live discovery/search on ≥1 real `*.atlassian.net` site through acli (no fixture in the path — asserted by the wrapper's runner audit).
- [ ] One transition → one typed Delta + one action; unchanged refresh → zero duplicates; x2 deterministic on the same window.
- [ ] The owner's verdict recorded VERBATIM; a bounce is a finding, fixed at the root.

## Test plan

- **Live:** the walk wrapper (story166-05-verify.sh) under dw capture; transcript + shots in assets/.
