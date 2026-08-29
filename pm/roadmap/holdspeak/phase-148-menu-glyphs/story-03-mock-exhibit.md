# HS-148-03 — The mock exhibit (the owner's variant gate)

- **Project:** holdspeak
- **Phase:** 148
- **Status:** ready
- **Depends on:** HS-148-01, HS-148-02
- **Unblocks:** HS-148-06
- **Owner:** unassigned

## Problem

The one genuinely-owner design input: glyph column A (Purist) / B
(Tribute-Plus) / C (Hybrid, recommended). The owner ruled "I'll see
mocks before a single live menu changes" — and the mocks must be
TRUTHFUL: real glass, not drawings.

## Scope

### In

- A shot rig (orchestrator-run) boots the real hub and photographs
  the SAME menus (Go, Desk, Object ghosted + populated, floor
  context with both submenus, the 393 Go) under each
  `data-menu-glyphs` state — A, B, C — at 1440, plus C at 393;
  before/after pairs against the audit shots.
- The exhibit is delivered to the owner (SendUserFile) with the
  recommendation and the one-line cost statement ("your verdict is
  a one-attribute flip, forever cheap").
- C ships as default per the settled design; any owner verdict
  flips the attribute in one commit.
- The exhibit + delivery record IS this story's evidence.

### Out

- Waiting indefinitely: delivery of the exhibit satisfies the gate
  under the owner's "go for it"; a later flinch is a redo by law.

## Acceptance criteria

1. Nine-plus truthful shots, cross-read clean (labels/keycaps agree
   across variants; only the column differs).
2. Exhibit delivered to the owner with the recommendation; the
   delivery is recorded in evidence.
3. The default state after this story is C unless the owner has
   already ruled otherwise.

## Test plan

The rig run itself (real hub, isolated HOME, fresh contexts, both
widths for C); pair manifest against
`assets/audit-menu-shots/`.
