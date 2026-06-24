# HSM-14-22 — The Living Desk: a fixed-angle 3D room with real height, light, and buildable barriers

- **Project:** holdspeak-mobile (canon for both surfaces; web does its own equivalent in HSM-16-04)
- **Phase:** 14
- **Status:** todo — opened 2026-06-24. The owner's escalation of the desk from a flat board to a
  **live physical system** seen in perspective. **This is the rendering-substrate decision** the rest
  of the DeskOS craft sits on.
- **Depends on:** the DeskOS shell + objects ([[story-19-the-desk]], [[story-20-the-desk-object-model]]).
  Enables the real form of [[story-21-desk-environments]].
- **Owner:** unassigned

## The vision (owner, verbatim-distilled)

> Pseudo-3D — or technically full 3D from a **fixed angle**: a person looking **down at their work
> desk**, not 90° top-down but more like **~82°**. The cards **know the surface — they lay on it** — but
> when you **pick one up it raises**, and it can **fall on others** and stack. And let the user **build
> barriers — walls out of pencils, erasers, clay** — to corral things. This is a **LIVE SYSTEM.**

## The substrate decision — SceneKit (fixed-camera true 3D)

The flat SpriteKit canvas (HSM-14-19) was the right 2D start. The live-system vision needs a third
dimension, and faking height/light/collision in 2D fights us forever. **We move the desk to SceneKit:**
a real 3D scene viewed by a **fixed camera at ~82° pitch** (the "looking down at your desk" angle).

SceneKit gives the whole vision natively:

- **Surface** — the desk is a lit 3D plane with a **PBR material** (marble, walnut, slate). This is what
  makes [[story-21-desk-environments]] *real* instead of wallpaper.
- **Light** — a `SCNLight` (the lamp) casts a real warm pool + real shadows. Environments = swapping
  the material + the light rig.
- **Height physics** — cards are thin textured nodes lying flat on the plane. **Pick up → the node
  rises** in z (lifts off the surface, its shadow grows + softens, a slight tilt toward the viewer).
  **Release → gravity drops it**; it can **land on another card and stack**, or slide and settle. Real
  `SCNPhysicsBody` collisions.
- **Buildable barriers** — the user pulls **pencils / erasers / clay** from a drawer and places them as
  **collidable physics nodes**: lay a pencil as a low wall, mound clay into a pen, build a corral. The
  objects respect them — roll up to them, stop, pile behind them. The desk becomes a space you *shape*.

The **DeskObject convention is unchanged** — objects are still objects, the gestures still mean the same
things; only the **rendering + physics gain a dimension**. Tap still opens (spill/window/read);
long-press reshapes; **lasso** projects the loop onto the surface to select; **windows** float above the
scene as a SwiftUI overlay (UI lives in 2D over the 3D room). Spill/file/bundle/Ask all carry over.

## What changes, concretely

- A new SceneKit desk scene replaces `DeskPhysicsCanvas` as the canvas (the SwiftUI shell, sidebar,
  windows, selection bar are unchanged — they sit *over* it). Cards render as flat textured nodes
  (reuse `DeskCardFace` → texture, now on a 3D quad). Real meeting data, not a tech demo.
- A fixed camera (~82° pitch), a desk plane + material, a light rig — all driven by the **active
  environment** (HSM-14-21). Switching environments re-lights the room.
- Touch: ray-cast from the camera to pick a card; raise it while dragging; release → physics. Pinch
  still zooms (dolly the camera); two-finger pan orbits slightly within a clamped range (never breaks
  the fixed-desk feel).
- A **barriers drawer**: pencil / eraser / clay primitives you place as collidable nodes; persisted per
  desk (layout class — per-device).

## Acceptance criteria

- [ ] The desk renders in **fixed ~82° perspective**; cards **lay flat on the surface** with correct
      perspective + real contact shadows.
- [ ] **Pick up raises** a card (lifts, shadow grows); **release drops it** under gravity; cards **land
      on and stack** on each other and settle believably.
- [ ] An environment's **material + light** drive the surface and shadows (ties [[story-21-desk-environments]]).
- [ ] The user can **build barriers** from pencils / erasers / clay that **objects collide with** and
      pile behind; barriers persist per device.
- [ ] All existing desk behavior still works over the 3D scene: tap-open/spill, long-press reshape,
      lasso-select, bundle, file, windows, Ask.
- [ ] Device-proven on the iPad Air M4 — the lift/fall/stack and a built barrier shown working on real
      metal ([[feedback_verify_on_device_not_seeded]]); frame rate holds with a full desk; reduce-motion
      respected.

## Test plan

- On device: fling/stack cards (they pile and settle), pick one up (it raises with a growing shadow),
  build a pencil wall and push cards against it (they stop + pile), switch an environment (the room
  re-lights). Confirm lasso/spill/windows still work over the 3D scene.
- Performance: a desk of ~30 card nodes + barriers holds frame rate on the M4.
