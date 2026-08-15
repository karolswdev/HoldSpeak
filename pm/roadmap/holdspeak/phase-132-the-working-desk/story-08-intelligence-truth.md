# HS-132-08 — Intelligence tells the truth

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** HS-132-06
- **Unblocks:** HS-132-14
- **Owner:** unassigned

## Problem

Four verified truth defects in the Intelligence surface:

1. **False ALL CLEAR.** Segment tabs call only `setActiveView` and never
   clear a dispatched `overdueOnly` filter
   (`IntelligencePullout.tsx:36-45,112`); after following the "N overdue"
   chip and returning via tabs, FollowThroughView hides every lane but
   Overdue and announces "ALL CLEAR — no follow-through yet" while real
   commitments exist (proven by vitest probe). Nothing names the active
   filter; no control clears it.
2. **Brief triage persists nothing.** Acknowledge/Defer only set local React
   state (`BriefView.tsx:48,91-95`); no endpoint, no localStorage — triage
   vanishes on reload/view-switch/close.
3. **A recorded week reads "Nothing material changed."** The Monday Brief's
   change collector only matches create/update/delete/transition/run/commit/
   complete method names (`monday_brief_service.py:15-24,198`); meeting
   lifecycle methods (start_capture, stop_capture, bookmark, import_meeting)
   match none, so meetings never appear in Changed.
4. **Aftercare is invisible without the mascot.** `aftercare_ready`'s only
   subscriber is the Qlippy block gated on presence+mascot
   (`AmbientLayer.tsx:130-166`, off by default); a meeting that just ended
   raises no live signal anywhere on the desk.

## Scope

### In

- Segment clicks own navigation state (reset to bare `{view}`); any active
  drill filter renders as a visible, dismissible token; ALL CLEAR is
  impossible while any lane holds cards.
- A small brief-triage shelf persisted server-side (acknowledge/defer per
  brief item), read back by `useIntelligenceAttention` so the dock badge
  reflects triage.
- A meetings collector for the brief's Changed section.
- `aftercare_ready` surfaces on the desk without the mascot (in-flow, e.g.
  the attention drawer), linking to the proposals.

### Out

- Daily Brief/Cadence merge (#450 Wave 2 — backlog); brief content redesign.

## Acceptance criteria

- [ ] The overdue drill filter is visibly named, dismissible, and cleared by
  segment navigation; the board can never read ALL CLEAR with live
  commitments (regression test from the audit's probe).
- [ ] Acknowledge/Defer survive reload and pullout close; the attention badge
  reflects them.
- [ ] A week containing recorded meetings lists them under Changed.
- [ ] With the mascot off, a finished meeting's pending proposals are
  discoverable from the desk within one click.

## Test plan

- vitest: navigation/filter-token behavior; shelf round-trip; attention
  badge.
- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_monday_brief_service.py tests/unit/test_brief_collectors.py --tb=short` plus new collector tests and shelf route tests.
