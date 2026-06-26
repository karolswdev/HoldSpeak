# HSM-14-24 — Nested zones: a boundary is a doorway (double-tap → zoom in → it IS the desk)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-24 on the owner's (excited) idea; **built 2026-06-24**
  (double-tap dive + camera descent, recursive path-based sub-zones, breadcrumb + double-tap-empty back,
  haptic transition). The feature that makes the DeskOS **fractal**: a fence/zone isn't just a wall, it's
  a way *in*. Device-arch compile + install done; the live dive-feel walk on the iPad is the last AC.
- **Depends on:** [[story-22-the-living-desk]] (the 3D desk + fences), [[story-23-the-deskos-shell]]
  (the shell), the fence/cluster-zone primitive — **the prerequisite drop-to-tag (a zone is a persisted
  place that holds cards) shipped 2026-06-24** (handover §7 #1); a zone now has contents to dive into.
- **Owner:** unassigned

## The idea (owner, verbatim-distilled)

> Once you establish a boundary — "this is where I keep X" — **double-tap** it and the camera **zooms in
> dramatically**, making IT the canvas, expanding it to a huge size, so THERE you get an **additional
> level of categorization**. And **each level is easily backable** from the next, so you end up back in
> the first state. This is the kind of stuff that makes it exciting.

## Why it matters

A boundary stops being a wall and becomes a **doorway**. Organization gains **depth**: a zone on your
desk ("Project Atlas") opens into its *own* desk, with its own objects, its own fences, its own
sub-zones — recursively. One gesture (double-tap) descends; one gesture (back) ascends. It's the
difference between a pegboard and a building. It also dovetails with the convention
([[story-20-the-desk-object-model]]): a **zone is a container DeskObject** whose `open` behaviour is
**`.enter`** — descend into it as a nested desk — beside the existing `.spill` / `.window` / `.read`.

## Scope

- **In:**
  - A **zone** is a fenced region with an identity (a cluster/tag). Double-tap inside it → the camera
    **dives**: a dramatic zoom + the zone expands to fill the desk, becoming a **nested desk** with its
    own surface, objects (the cards filed into that zone), and room for its own fences/sub-zones.
  - A **breadcrumb + Back**: each level is clearly backable ("Desk › Project Atlas › Q3"), one gesture
    (or the breadcrumb) pops up a level, all the way to the root. State per level is preserved.
  - **Membership = the zone's contents.** A card dropped into a zone (the drop-to-tag primitive) is what
    appears inside that zone's nested desk. Descending shows exactly those objects.
  - A **smooth, gamified transition** (the dive/ascend animation) — it should *feel* like falling in and
    climbing out, with haptics.
- **Out:** the full drop-to-tag tagging engine is its own slice (the prerequisite); cross-device sync of
  the nesting tree (folds into Phase 16 organization sync — a nested zone is just a directory/KB tree).

## Acceptance criteria

- [x] Double-tapping a zone dives in: camera zoom + the zone becomes a full nested desk. *(built + FIXED
      2026-06-24 after a device walk showed it dead: `cardNode` was eating the tap by treating the zone node
      as a card. Now a **single tap** on a zone dives — double-tap still works too — via `diveInto` camera
      rush+zoom → `onDive`; the desk swaps to the zone's contents; a `›` cue marks the placard.)*
- [x] The nested desk shows the zone's members (the cards filed into it) and supports its own
      fences/sub-zones — recursively (at least 2 levels deep proven). *(built: path-based containers —
      drawing inside "Atlas" makes "Atlas/Q3"; `deskZones` is level-scoped; nested-desk render composed.)*
- [x] A breadcrumb + a Back gesture pop up exactly one level, to the root, with each level's state intact.
      *(built: `DeskBreadcrumb` jump-to-any-crumb + double-tap-empty-desk climbs out; `deskPath` drives it.)*
- [x] The dive/ascend is a smooth, dramatic, haptic transition — not a cut. *(built: `syncLevel` settles the
      camera home from a directional offset; medium/light haptics on dive/ascend. **Timing tuned on device.**)*
- [ ] Device-proven on the iPad Air M4 ([[feedback_verify_on_device_not_seeded]]). *(installed; live walk
      pending an unlock — the dive FEEL is the one thing the static renderer can't show.)*

## Test plan

- On device: fence a zone, file two cards into it, double-tap → dive into its nested desk showing those
  two cards; fence a sub-zone inside, file one card, double-tap again (level 2); Back twice → root, state
  preserved. The transition feels like falling in / climbing out.

## Notes

- The nesting tree maps cleanly onto the **organization** layer (directories/KBs are already a tree):
  a zone == a directory/KB; a sub-zone == a child. So this reuses the filing model and will sync via
  Phase 16 for free. Recursive desks, one organization tree underneath.
