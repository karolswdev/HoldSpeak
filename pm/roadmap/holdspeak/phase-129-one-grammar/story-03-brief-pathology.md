# HS-129-03 — The Brief pathology and Intelligence polish

- **Project:** holdspeak
- **Phase:** 129
- **Status:** in-progress
- **Depends on:** HS-129-01
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

A window must never be taller than the desk. Audit B's P0: opening
Intelligence → Brief with real data computes a 9,710 px window — no internal
scroll region, the resize grip at y=9,753, content and foot unreachable,
maximize does not repair it. The pullout's content-sized card behavior
(`fitContent`) has no height cap once Brief's real material arrives.

### What changes

1. The Intelligence pullout window height is capped by the working band
   (like every arranged window); `.desk-pullout-body` scrolls the Brief
   material inside it. Diagnose whether the defect is the `is-card` height
   release (pullout.css:16-22), a missing `min-height: 0` in the Brief
   stack, or the fitContent seed — fix at the seam, not per-view.
2. Brief headline overflow (found in the 2026-08-08 populated walk): the
   `.intelligence-*` headline wraps (`overflow-wrap`) instead of clipping at
   the pullout edge at desktop widths.
3. The `← BACK` affordance renders only when navigation history exists.
4. Follow-through and Receipts views re-verified unchanged (they were
   correct in the walk).

## Acceptance criteria

1. Brief with 190+ real items opens at a working-band-capped height; the
   body scrolls; grip, foot, and all content are reachable; maximize and
   small-resize behave.
2. The Brief headline never overflows the pullout horizontally at any width
   ≥ the window minimum.
3. BACK is absent on first open, present after a cross-link drill, and
   returns correctly.

## Test plan

- Web: component test for capped height + scrollable Brief body with a
  large seeded payload; BACK visibility test.
- Walk: Playwright against the seeded desk (brief with 193 changes):
  open Brief, assert window height ≤ viewport working band, scroll to
  bottom, screenshot at 1440 and 393.
