# HS-116-15 — The walk

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-10, HS-116-11, HS-116-12, HS-116-13, HS-116-14
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every surface introduced or modified in Phase 116 passes a
screenshot walk at both viewports (1440 desktop, 393 mobile).
The walk proves that the system works end-to-end: a workbench
is created from a template, configured in-world, items are added
by voice and text, grounding is attached, a run is triggered, items
show live progress, results render with egress badges, and the
constitutional context editor is functional. No surface ships unseen.

**Articles served:** VIII (native-grade craft — every glass is
first-class), IX (proof over claim — UI ships only after it was
seen).

## Deliverables

1. **Playwright screenshot walk.** Automated shots at 1440×900 and
   393×852 of:
   - Template picker (with all 4 templates + blank)
   - Workbench window after template instantiation (configured,
     with starter items)
   - Configuration panel expanded (agent picker, target picker,
     schedule presets, skills section)
   - Item card in all states: pending, running (with LedMeter),
     done (with result + egress badge), failed, dismissed
   - Expanded item with body, grounding chips, rendered result,
     Keep and Re-run verbs
   - Run history wing with past run receipts
   - Composer with mic button, grounding section, priority cycle
   - Constitutional context editor with content, revision, token
     estimate
   - Voice command proposal strip (if achievable in automation)
   - The desk stage with workbench objects (cartridge sprites)

2. **End-to-end proof.** At least one shot sequence showing:
   - Create Morning Brief workbench from template
   - Configure it (pick agent, pick target)
   - Trigger manual run
   - See items progress from PENDING → RUNNING → DONE
   - Open a completed item, see the result with egress badge
   - Open run history, see the receipt

3. **Material audit.** Each screenshot verified against:
   - Bevel box-shadow on chips and cards
   - Keyline on window borders
   - Correct token consumption (fills, heads, borders)
   - Egress lamp colors (green/amber/red)
   - Mono typeface in traffic surfaces
   - No prose, no modals, no tutorial text

4. **Evidence.** Screenshots saved to `assets/hs-116-15/` and
   referenced in `evidence-story-15.md`.

## Test plan

- Playwright walk runs against the real hub with a real inference
  target (at minimum this_machine).
- Every screenshot reviewed for material violations.
- Both viewports pass.
