# HS-168-03 - The Connections face: Settings → Connections

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** HS-168-01, HS-168-02
- **Unblocks:** HS-168-04, HS-168-05
- **Owner:** unassigned

## Problem

There is no place on the desk that shows what is connected and what
to do about it. Settings → Integrations (SettingsCore.tsx:1043) is
credentials + mesh; the calendar hides under Meetings; GitHub and
Jira have no home at all.

## Scope

- **In:** the D1 face built to the ratified mockups from the barrel
  only: the Settings module the design named (rename or new; every
  `openSurfaceWindow("configure-settings", …)` caller from the 01
  census updated, deep links tested); one ChoiceCard per tool with
  StateChip + ProvenanceChip + the ONE next verb; the sign-in fold
  (mono well, COPY as a TransportKey, Recheck); Jira Add account as
  the 166 fold; the calendar card routing to the 146 flow; the
  model-hosts LINK card to the 156 front door; CREDENTIALS and MESH
  groups kept with their tests; EgressChip on every check naming the
  host; absent/degraded states; both widths; the mic where text is
  typed. Reads `GET /api/connections` only.
- **Out:** the interview (04); any credential capture.

## Acceptance criteria

- [ ] The face composes barrel species only (zero hand-rolled rows, zero sentences); the four states render as designed at 1440 and 393.
- [ ] Every deep-link caller updated and pinned; the credentials + mesh tests green.
- [ ] Glass rig shots read by the orchestrator at true size before the flip.

## Test plan

- **Vitest:** web/src/pages/cores/__tests__/connections*.test.tsx (states, verbs, deep links).
- **Glass:** tests/e2e/test_hs168_connections_glass.py (build-first; both widths; the fold; recheck).
- **Baseline:** `uv run python scripts/check_web_baseline.py --run` zero branch-new.
