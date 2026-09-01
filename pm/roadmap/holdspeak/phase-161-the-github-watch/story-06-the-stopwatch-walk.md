# HS-161-06 - The stopwatch walk: five minutes, measured, and one real-metal leg

- **Project:** holdspeak
- **Phase:** 161
- **Status:** backlog
- **Depends on:** HS-161-04 (rig vs the wire; face legs after 05's functional)
- **Unblocks:** HS-161-07
- **Owner:** unassigned

## Problem

SETFLOW-001: prepared-fixture completion under five minutes without
JSON/query authoring — the bar is a NUMBER (the 156-07 discipline:
wall clock, itemized segments). VAL-INT-002's law made local. Plus
the SRS's double warning: fixtures never fake READINESS — so one
real-metal leg runs the true gh against a real repository.

## Scope

- **In:** `tests/e2e/test_hs161_github_glass.py`:
  (1) THE STOPWATCH (fixture runner): outcome answer → signals →
  GitHub candidate appears (connected fixture) → clarify repo →
  LIVE test (fixture PRs render: count + samples + conditions) →
  activate → populated Now with the watch binding → wall clock per
  segment into `assets/story-06-stopwatch.json`; the bar asserted
  < 300s (expect seconds — the 156 precedent: the machinery's cost,
  not the human's reading speed).
  (2) THE AUTH-DEGRADED LEG: unauthenticated fixture →
  owner_action_required card + Recheck → recover (flip the fixture)
  → the exact setup step resumes (SETFLOW-003 on glass).
  (3) THE EVALUATION LEG: a changed fixture snapshot → evaluate →
  the Delta review shows the PR transition evidence-linked (the
  compounding proof on glass).
  (4) THE REAL-METAL LEG (marked, skip-clean without auth/network):
  the REAL gh against the REAL karolswdev/HoldSpeak repo — probe,
  discover (bounded), validate, one live snapshot test with real
  PR data rendered; NO baseline/activation against the real repo
  (read-only, receipted). Shots: the wizard states, the live test
  card, the stopwatch summary, degraded auth — assets/story-06-shots/.
- **Out:** writes, scheduling.

## Acceptance criteria

- [ ] The stopwatch bar met and MEASURED (segments itemized in the JSON; the number in the story record).
- [ ] Auth-degraded and evaluation legs deterministic ×2; overflow zero; shots >20KB.
- [ ] The real-metal leg passes live on this machine (gh authenticated) and skips clean elsewhere; every real read receipted.

## Test plan

- **E2E:** the four legs; build-first; playwright env; deterministic ×2 (fixture legs).

## Notes / open questions

- The real-metal leg reads only public/own-repo data through the owner's own gh auth — the same trust the desk already exercises via GitHubWatchSource.
