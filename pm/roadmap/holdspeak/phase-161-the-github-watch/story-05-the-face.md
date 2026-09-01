# HS-161-05 - The face: Check connection → Discover → Clarify → Test, honestly

- **Project:** holdspeak
- **Phase:** 161
- **Status:** in-progress
- **Depends on:** HS-161-04 (scaffolding may start against 04's frozen wire)
- **Unblocks:** HS-161-07
- **Owner:** unassigned

## Problem

§13's one functional vocabulary: Check connection → Discover → Test
→ Activate. WEB-CR-004/005: each external candidate enters a bounded
provider flow and returns without losing setup state; provider state
distinguishes checking/ready/connection_required/capability_missing/
partial/unavailable/failed with ONE exact next action. SETFLOW-003:
missing auth preserves setup, names the recovery, offers Recheck;
GitHub NEVER appears active before a passing test. And the arc's
first egress badge: every GitHub call shows local+cloud at the point
of decision (WEB-VIS-005 — reuse the existing badge species; no
privacy novels).

## Scope

- **In:** inside the setup feature: the provider wizard step
  (connection status card with the state vocabulary + ONE next
  action; Recheck; the discovery list (searchable, bounded) + the
  typed-repo fallback input; the clarify step gaining repo scope);
  GitHub candidate cards joining the suggestion grid (ChoiceCardShell
  — the library owns material; the egress badge ON the card and on
  the test result: these reads leave the machine); the §8.1 test
  display (repo, query in plain words, count, ≤5 PRs, present
  conditions, observed time, typed errors); the activation review
  already handles specs — verify the github spec renders honestly
  (plain-words conditions grew in 159 — extend the vocabulary for
  the PR condition fields). Keyboard/a11y per the standing laws;
  fixtures mined from 04's integration tests. Then BEAUTY + shots →
  THE OWNER'S VERDICT closes this story.
- **Out:** writes, scheduling UI, Jira.

## Acceptance criteria

- [ ] The four-word vocabulary on the glass; every provider state has its named token + ONE next action (WEB-CR-005).
- [ ] SETFLOW-003 on the face: unauthenticated → owner_action_required card + Recheck; setup state preserved through the round-trip; never-active-before-passing-test enforced visually and in state.
- [ ] The egress badge (local+cloud · github.com) at the candidate card, the test action, and the test result (WEB-VIS-005/Art III.2) — reusing the existing badge component.
- [ ] Discovery + typed fallback both reach a validated scope from the keyboard; zero modals; mic on new inputs.
- [ ] check green; baseline zero branch-new; SHOTS + THE OWNER'S VERDICT: PASS recorded verbatim.

## Test plan

- **Web unit:** wizard states, recheck, discovery/fallback, badge presence, plain-words PR conditions.
- **Glass:** rides 06 + face shots.
- **Manual:** the owner's verdict — the closing gate.

## Notes / open questions

- Find the existing egress badge component FIRST (the desk has one — Art III.2 is old law); never build a second species.
