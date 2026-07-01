# HS-71-03 — Objects that float (the diorama's heartbeat)

- **Status:** done
- **Priority:** HIGH (the moment it becomes a world)
- **Depends on:** HS-71-01, HS-71-02
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## Goal

Turn each primitive from a card-list row into a **floating pixel-art object** on
the stage, with the full "alive" treatment the iPad gives it. This is the story
where `/desk` stops being a document.

## Scope

- Render every `this.items[kind]` entry as a stage object (Alpine `x-for` over
  the flat item list) placed on the stage: the sprite (`spriteFor`), a label,
  and per-kind tint.
- The **alive** treatment per object, matching `DioHeroVisual`:
  - **float** — vertical bob (`sin`, ~0.9 Hz) + subtle breathe scale + slow tilt,
    via **CSS keyframes with a per-object phase** (`--phase` custom prop from the
    id hash) so N objects animate on the GPU with no rAF loop.
  - **detached ground shadow** — a blurred ellipse beneath, offset so it separates
    from the object as it bobs (the "floating above a surface" cue).
  - **glow pool** — a per-kind radial halo under the sprite.
  - **drop shadow** on the sprite itself.
- The old grouped card-list DOM is retired for the stage render (the section
  labels/counts may survive as a quiet legend/HUD, not stacked cards).
- All object CSS is `<style is:global>` (Alpine-injected).
- Reduced-motion: objects rest (no bob), shadows/glow static.

## Proof required

Screenshots of the populated stage (seeded meetings/notes/kbs/agents) as
floating objects with shadows + glow; a short capture showing the float; the
side-by-side vibe check against the iPad desk noted. Reduced-motion verified.
Performance sane with ~20+ objects (CSS-driven, no rAF).

## Done

Shipped and screenshot-proven. `/desk` now renders every primitive as a floating
pixel-art object: `worldObjects()` flattens all kinds, `objStyle` auto-lays-them
out with per-object float phase/tilt/scale + glow tint, and each `.desk-obj`
floats (`desk-bob` CSS keyframes, no rAF) with a per-kind glow and a DETACHED
ground shadow that softens as it lifts. The old card-list + authoring UI is
preserved under a collapsed "Browse as a list" `<details>`. A 12-object mixed
desk (meetings/notes/kbs/agents/directory, seeded via real `/api/*` POSTs)
proves it. `is:global` CSS; reduced-motion-safe; zero page errors; suite green.
See [evidence-story-03.md](./evidence-story-03.md).
