# HS-113-09 - The static desk

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The Desk must feel like Workbench 2.0 — icons are static handles on
a grid, not animated mascots in a diorama. Today every world icon
bobs on a 4.6-second cosine cycle, hovers with additive glow instead
of the `_sel` sprite, spawns with a fractional-scale materialize
animation, and eighteen decorative motes drift across the stage. All
of this must go. When this story ships, the desk at rest is STILL —
a precise, pixel-true workspace where objects sit where you put them.

**Articles served:** VIII (native-grade craft, 1:1 pixel art, no
fractional scaling), VII (quiet chrome — motion explains changes,
idle content does not move).

**Canon:** ICON-DISCIPLINE.md ("an icon is a live handle, not a
mascot"), DESK_GRAMMAR.md law 1 ("no fractional scaling, tilting,
or importance-by-size").

## Ground (from the audit)

**Nine motion violations found in the codebase:**

1. **Perpetual idle bob** — `engine.ts:774-806`. Every non-dragged
   sprite follows a 4.6-second cosine cycle: art container moves
   0→-9px→0, shadow shrinks and fades in sync. This is the reported
   "icons hover and pulsate."

2. **Per-object desynchronized phase** — `world.ts:146-155`.
   `objMotion()` generates a stable per-icon phase, intentionally
   desynchronizing each icon's float. Comment says "the positional
   bob keeps the desk alive."

3. **Motion values in scene model** — `sceneModel.ts:160-180`. Each
   scene object receives `phase`, `tilt`, `scale` from `objMotion()`.
   Tilt and scale resolve to zero/one but phase feeds the bob.

4. **Hover glow and highlight** — `engine.ts:452-459,807-819`.
   Hovered objects get additive glow (0.50→0.82 alpha) plus a
   highlight sprite. Should use the `_sel` state image instead.

5. **Spawn materialize** — `engine.ts:819-828,1326-1330`. New nodes
   scale from 35% through overshoot to 100% over 500ms. Fractionally
   scales pixel art.

6. **Animated NEW ring** — `engine.ts:533-545,600-623,829-843`.
   Ring expands 70%→155% while fading, three 1.1-second beats.

7. **Zone/drawer hover lift+scale** — `engine.ts:693-748,846-850`.
   Hover: rise 2px. Drop-ready: rise 4px, scale 1.04. Should use
   `_sel` sprite instead.

8. **Decorative drifting motes** — `engine.ts:754-792`. Eighteen
   random motes drift upward across the stage. Pure decoration.

9. **Dive camera fractional scale** — `desk.css:1302-1333`.
   `.desk-world.dived` scales from `scale(1.06)` to `scale(1)`,
   temporarily fractionally scaling every sprite.

**Additional chrome motion (lower priority):**
- Agent-rail hover scale to 1.08 + working halo pulse:
  `desk.css:1414-1449`.
- Recording status glow-ring pulse: `desk.css:331-346,1549-1557`
  (conflicts with its own comment "square, no glow").
- Dock chip scale/fade entrance: `desk.css:3576-3591`.
- Stale magnification CSS (`--dock-mag`): `desk.css:3597-3610`.

## Method

1. **Kill the idle bob:**
   - In `engine.ts` ticker loop (~774-806): remove the cosine
     vertical offset. Art container y-offset stays at 0. Shadow
     stays at its rest scale/alpha.
   - In `world.ts:146-155`: remove `objMotion()` or make it
     return zeroes. Remove the "keeps the desk alive" comment.
   - In `sceneModel.ts:160-180`: stop passing motion phase.

2. **Replace hover glow with `_sel` sprite:**
   - In `engine.ts:452-459,807-819`: on hover, swap to the `_sel`
     sprite texture (already exists per ICON-DISCIPLINE). Remove
     additive glow alpha and highlight sprite.
   - Selection should also use `_sel` sprite (it may already).

3. **Replace spawn materialize with instant appear:**
   - In `engine.ts:819-828,1326-1330`: newly created nodes appear
     at full size, full opacity, no animation. Pixel art appears
     at 1:1, never fractionally scaled.

4. **Kill the NEW ring animation:**
   - In `engine.ts:533-545,600-623,829-843`: the NEW badge can
     stay as a static label. Remove the expanding/fading ring.

5. **Replace zone hover lift+scale with `_sel` sprite:**
   - In `engine.ts:693-748,846-850`: on hover, swap to zone's
     `_sel` sprite. No rise, no scale. Drop-ready target lights
     with its `_sel` sprite per drop law.

6. **Remove decorative motes:**
   - In `engine.ts:754-792`: delete the mote creation and update
     loop. The desk floor is clean.

7. **Fix dive camera:**
   - In `desk.css:1302-1333`: remove `scale(1.06)` on `.dived`.
     Use opacity transition only, or a clean cut. No fractional
     scaling of sprites.

8. **Fix agent-rail hover:**
   - In `desk.css:1414-1449`: remove `scale(1.08)` on hover.
     Remove infinite box-shadow pulse on working avatar.

9. **Fix recording status:**
   - In `desk.css:331-346,1549-1557`: remove the glow-ring halo.
     Keep the flat brightness pulse (explicitly permitted by
     ICON-DISCIPLINE for the record key).

10. **Clean up stale dock magnification CSS:**
    - In `desk.css:3597-3610`: remove `--dock-mag` transform
      references (component code confirms magnification was removed).

## Test plan

- Visual: load the desk with 10+ objects. Wait 30 seconds. NO
  object moves. The desk at rest is perfectly still.
- Visual: hover an icon. It shows its `_sel` sprite. No glow,
  no additive highlight, no scale, no rise.
- Visual: create a new object. It appears instantly at 1:1. No
  scale-in animation.
- Visual: hover a zone/drawer. It shows its `_sel` sprite. No
  lift, no scale.
- Visual: no drifting motes anywhere on the desk.
- Visual: dive into a zone. No fractional scale transition.
- Unit: `objMotion()` returns zero phase/no motion (or is removed).
- Regression: all existing GL tests pass.
- Screenshot walk: 1440px — desk with 15+ objects at rest. Must
  look like Workbench 2.0: static, precise, grid-aligned objects
  with no ambient animation.
- Screenshot walk: 393px — same stillness on mobile.
- Performance: removing the idle bob should REDUCE GPU load (the
  ticker loop does less work per frame).
