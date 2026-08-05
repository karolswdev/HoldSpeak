# HS-116-09 — The walk

- **Project:** holdspeak
- **Phase:** 116
- **Status:** backlog
- **Depends on:** HS-116-08
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every surface introduced or modified in Phase 116 passes a
screenshot walk at both viewports (1440 desktop, 393 mobile). The
walk proves that the workbench window, constitutional context
editor, template picker, item composer, skills surface, run
receipts, morning brief notification, and egress lamps all render
correctly in the Signal Workbench material language. No surface
ships unseen.

**Articles served:** VIII (native-grade craft — every glass is
first-class), IX (proof over claim — UI ships only after it was
seen).

## Deliverables

1. **Playwright screenshot walk.** Automated shots at 1440×900 and
   393×852 of:
   - Workbench window (empty state)
   - Workbench window (with items, mixed statuses)
   - Template picker (grid of template cards)
   - Constitutional context editor
   - Item composer (with grounding attached)
   - Expanded item (with agent result + receipt)
   - Morning brief notification (desk notification)
   - Morning brief artifact (opened on desk)
   - Skills section in recipe editor (active + draft skills)
   - RunsOnPicker cycling through targets on a workbench

2. **Material audit.** Each screenshot is verified against:
   - Bevel box-shadow on chips and cards
   - Keyline on window borders
   - Correct token consumption (fills, heads, borders)
   - Egress lamp colors (green/amber/red)
   - Mono typeface in traffic surfaces
   - No prose, no modals, no tutorial text

3. **Evidence.** Screenshots saved to `assets/hs-116-09/` and
   referenced in `evidence-story-09.md`.

## Test plan

- Playwright walk runs against the real hub (not a mock server).
- Every screenshot reviewed for material violations.
- Both viewports pass.
