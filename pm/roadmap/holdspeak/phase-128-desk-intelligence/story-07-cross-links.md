# HS-128-07 — Cross-link drill paths

- **Project:** holdspeak
- **Phase:** 128
- **Status:** backlog
- **Depends on:** HS-128-05, HS-128-06
- **Unblocks:** HS-128-08
- **Owner:** unassigned

## The thesis (the bar)

The three views form one investigation, not three destinations. Every link
moves through the pullout or opens the relevant Desk primitive in world.

### What changes

1. Make a Brief item switch to Follow-Through and focus its matching card.
2. Make a card's provenance switch to Receipts and open its receipt detail.
3. Make a receipt's affected-work chip open its target primitive window.
4. Add pullout-local back navigation that restores the previous view, focus,
   filters, and detail state.

## Acceptance criteria

1. All three forward links resolve their actual related record by stable ID.
2. No drill path uses a route, modal, or duplicate pullout.
3. Back restores the prior in-pullout state rather than resetting to Brief.
4. Missing/deleted relation fails by name in the existing in-flow receipt path.

## Test plan

- Web: fixture the three relation types and assert view/focus/detail transitions.
- State: traverse forward and back across each path with state restoration.
- Walk: capture all three drill paths from real Desk surfaces.
