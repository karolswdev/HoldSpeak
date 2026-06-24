# HSM-14-21 — Desk Environments: themeable surfaces, real light, and an environment builder

- **Project:** holdspeak-mobile (canon for both surfaces; web parity via Phase 16 / HSM-16-04)
- **Phase:** 14
- **Status:** todo — opened 2026-06-24 on the owner's direction: the desk is a **place**, not a flat
  canvas, and it ships **multiple themed environments** plus a **builder**.
- **Depends on:** the DeskOS shell ([[story-19-the-desk]]), the DeskObject convention
  ([[story-20-the-desk-object-model]]). PixelLab for pixel-art props; free CC0 libraries for materials.
- **Owner:** unassigned

## The vision (owner, verbatim-distilled)

> Multiple themes — like a **lamp casting light on a marble table, with a mousepad** and so on. This is
> the level we're going with. All supplied by **free assets you'll find**. At least **3 environments**,
> and an **environment builder. OBVIOUSLY.**

The desk is an atmosphere you choose and live in. Pixel-art **objects** (cassette / cartridge / crystal)
resting on a **rich material surface** under **real light** is the signature contrast — playful pieces,
premium room.

## What an "environment" is — the layers

An environment is a small declarative composition (data, not code) of:

1. **Surface** — the desktop material the objects rest on: polished marble, walnut, slate, brushed
   metal, glass. A tiled PBR/photo texture with a subtle normal/spec sheen.
2. **Light** — the room's lighting: a warm desk lamp casting a soft **pool of light** (a radial warm
   gradient + a long soft shadow direction), a cool LED strip, a green banker's glow, a hard spotlight.
   Light defines the mood more than anything; objects cast shadows consistent with it.
3. **Mat / props** — a **mousepad / desk mat** the cards can snap to, plus tasteful props (a lamp model,
   a mug, a pen cup) placed in the scene, non-interactive set-dressing.
4. **Palette + ambiance** — the accent + chrome tint, a vignette, grain, depth-of-field haze — the color
   grade that makes the Signal UI sit in the room.

Every object's drop-shadow + the canvas grade derive from the active environment, so swapping themes
re-lights the whole desk, not just the wallpaper.

**Realized on the Living Desk substrate ([[story-22-the-living-desk]]).** Once the desk is a fixed-angle
3D SceneKit room, an environment is literally a **material + light rig**: the surface is a PBR material,
the lamp is a real `SCNLight` casting real shadows. The 3 environments below become 3 light/material
rigs; the builder composes them. (HSM-14-22 is therefore the dependency — see [[DESK_BUILD_SEQUENCE]].)

## The 3 starter environments

1. **Marble & Lamp** (the owner's exemplar) — polished white/grey marble, a warm desk lamp pooling light
   from the upper-left, a tan leather mousepad, deep soft shadows, dark studio surround. *Executive.*
2. **Walnut Workbench** — warm walnut wood grain, a green **banker's lamp** glow, a cork desk mat, brass
   accents, cozy low light. *Craftsman.*
3. **Midnight Carbon** — dark slate / carbon-fibre surface, a cool LED edge-glow, an RGB-rimmed gaming
   mousepad, the existing **Signal** dark vibe elevated. *Sleek/default.*

## The environment builder

A real composer (a window/app on the desk, per the convention): pick **surface**, **light**, **mat**,
**props**, **accent**, **ambiance** from supplied pieces; live-preview on the real desk; **save** as a
named custom environment that joins the theme switcher. Built from the same supplied asset packs — the
builder is just exposing the composition the 3 presets already use.

## Free asset sourcing (real, commercial-safe)

**Two asset kinds, two sources:** flat **materials** (surfaces/mats) come from texture libraries; **3D
props** (the lamp, mug, plant, pen cup) and **modular building pieces** come from **poly.pizza** — a huge
CC0/CC-BY library of real glTF models. The lamp becomes an *actual 3D model that emits the light*, not a
faked gradient — that is what makes the room real.

- **poly.pizza** (CC0/CC-BY glTF models) — the primary **3D prop + building-block** source. Owner-picked
  examples, all **CC0 / public domain**:
  - **"Light Desk"** by Quaternius — the **desk lamp** prop (the model the environment's `SCNLight`
    lives inside).
  - **"Modular Road Kit"** (Kenney) + **"Road Bits"** (Kay Lousberg) — **modular snap-together pieces**:
    the real basis for the **barrier/wall building set** ([[story-22-the-living-desk]]), elevating
    "a pencil" into a proper modular construction kit.
  - …plus mugs, plants, pen cups, books for set-dressing — "poly.pizza has a ton of stuff."
- **ambientCG** (ambientcg.com) — CC0 PBR **materials**: marble, walnut, slate, leather, carbon — the
  desk **surfaces + mats**.
- **Poly Haven** (polyhaven.com) — CC0 textures + **HDRIs** (the `lightingEnvironment` IBL fill).
- **PixelLab** (vendored) — matching **pixel-art** props where a pixel piece reads better than a model.

**Asset pipeline:** poly.pizza glTF/GLB → **USDZ** (Reality Converter / `usdzconvert`) → bundled → loaded
natively by SceneKit (`SCNScene(named:)` / Model I/O). Record every asset + license in
`assets/CREDITS.md`. Prefer CC0; credit CC-BY.

Aesthetic call: **photoreal material surfaces + real 3D props under real light**, with **pixel-art
objects** (cassette/crystal) as the cards on top — the contrast is the brand (carries the
[[story-19-the-desk]] "pixel objects on premium chrome" note forward).

## Sync / taxonomy note

A built environment is a **small composition (data)** — it can sync as a **preference/asset** across the
mesh so your room follows you (under Phase-16's model; *not* layout, *not* large binaries — the textures
ship with the app, the composition is a few ids). The **active theme** is a soft preference. Decided for
real when Phase 16 wires preferences; here it's just noted so the builder saves portable data.

## Acceptance criteria

- [ ] An environment system: the canvas background, surface, light pool, mat, and **every object's
      shadow + the color grade** derive from one active environment definition.
- [ ] **3 shipped environments** (Marble & Lamp, Walnut Workbench, Midnight Carbon), switchable live.
- [ ] An **environment builder** that composes surface/light/mat/props/accent, live-previews on the real
      desk, and saves a named custom environment into the switcher.
- [ ] Assets are CC0/permissive with provenance recorded in `assets/CREDITS.md`.
- [ ] Device-proven on the iPad Air M4 (the switch re-lights the desk for real — not a seeded shot;
      [[feedback_verify_on_device_not_seeded]]). Reduce-motion / performance respected.

## Test plan

- On device: switch all 3 environments — the surface, the light pool, the mat, and the object shadows
  change cohesively; build + save a custom one and it persists + re-selects. Frame rate holds with a
  full desk of objects.
- Asset hygiene: `assets/CREDITS.md` accounts for every bundled texture/prop with its license + source.
