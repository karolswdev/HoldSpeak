# HS-128-08 — Attention badges and notifications

- **Project:** holdspeak
- **Phase:** 128
- **Status:** done
- **Depends on:** HS-128-07
- **Unblocks:** HS-128-09
- **Owner:** unassigned

## The thesis (the bar)

Intelligence earns attention through a small honest signal: readiness, overdue
work, and review are projections of durable state, not a notification system.

### What changes

1. Show a sunrise dot on the dock icon when a new Brief is ready.
2. Show overdue Follow-Through as a red numeric dock badge.
3. Expose the receipt review queue as a distinct review marker.
4. Project the same state into `AttentionDrawer` using its established rows and
   actions, with no duplicated truth store.

## Acceptance criteria

1. Badge precedence and counts derive from current service projections.
2. Read/acknowledge and follow-through verbs refresh the visible signals.
3. AttentionDrawer and dock agree on the represented overdue and review state.
4. Zero state is quiet: no red zero, stale dot, or invented notification.

## Test plan

- Web: test brief-ready, overdue, review, and zero-state projections.
- Integration: mutate each backing service state and assert dock/drawer refresh.
- Accessibility: assert numeric badges retain a usable text label.
