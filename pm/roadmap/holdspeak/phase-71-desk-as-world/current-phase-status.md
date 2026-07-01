# Phase 71 — The Desk, as a World (the web diorama)

**Status:** IN PROGRESS (5/8) — 2026-07-01. Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

**Last updated:** 2026-07-01 (**opened + scaffolded** on owner direction. After Phase 70 shipped
(legible surface, four doors), the owner said the web still feels "nowhere near the look and feel of the
iOS app". Shown the two "Desks" side by side — the iPad's 2.5D spatial diorama vs. the web's flat
card-list — the owner chose the full fix: **port the diorama to the web.** A technical map (the scaffold
Explore) confirmed the good news: the web `/desk` already loads every primitive live from the same
`/api/*` endpoints the iPad uses, so this is **primarily a rendering change, not new plumbing**. Eight
stories authored; branch `phase-71-desk-as-world` on open.)

## The thesis

Phase 69 matched the design-system tokens; Phase 70 fixed the information architecture; but the web still
*feels* like a document while the iPad *feels* like a world. The gap is **paradigm**: a 2.5D spatial
diorama (warm atmosphere, hand-drawn floating sprite objects, drag/file/dive, an in-world mascot) vs. a
flat page-based card-list. Phase 71 ports the diorama to the web `/desk`, reusing the existing `/api/*`
primitive data layer, so the web finally has the iPad's felt world. Only `/desk` changes; the two-mode
cockpits (Home / Dictation / Meetings) stay clean, fast dashboards (owner call).

## What the target is (traced from `apple/App/MeetingCapture/DeskDioramaStage.swift`)

- Warm atmosphere: `DioPal` vertical gradient (`#0B0D12`→`#16111F`→`#090A0E`) + an animated warm radial
  spotlight (`~50%,40%`, accent-tinted, `sin`-pulsed, plus-lighter) + rising dust motes. Accent `#FF6B35`.
- Objects that float: each primitive is a bundled pixel-art PNG sprite (`DeskSprite`) with bob/breathe/
  tilt float, a **detached** soft ground shadow, a per-kind glow pool, and a drop shadow.
- Free placement in unit space (`positions[id]`, persisted `hs.diorama.pos`, per-device) with density-
  aware auto-layout (`looseHome`: more items → more columns + shrink to a floor).
- Zones (== web `directory`) as painted shelf-trays you drag onto to file and dive into (a camera level).
- Qlippy (`DioCompanion`) living in the corner with its own shadow.

## The seam it builds on (traced from `web/src/pages/desk.astro` + `desk-app.js`)

- Alpine factory loaded via `?raw` + `new Function`; `loadAll()` already pulls every kind from
  `/api/meetings`, `/api/sync/pull`, `/api/notes`, `/api/agents`, `/api/kbs`, `/api/directories`,
  `/api/chains`, `/api/workflows`, `/api/profiles`, `/api/companion/status`, normalized to
  `this.items[kind] = [{kind,id,title,…}]`. **No new read API required.**
- Kinds: `meeting, artifact, note, agent, chain, workflow, directory, kb, coder` (+ `game`);
  `web/src/lib/primitives.ts` + `desk.astro` META. Web `directory` == iPad `zone`.
- Geometry is **local-only** on both surfaces (never synced). Web keeps positions in `localStorage`.
- Sprites: only Qlippy is under `web/public/` today; a story copies the primitive PNGs from `apple/App/`
  into `web/public/desk/sprites/` + a djb2 stable-hash picker (matching `SpriteStore.stableHash`).

## Scope

- **In:** the eight stories below — the room, the sprite pipeline, floating objects, free placement,
  zones+dive, in-world Qlippy + create/open, docs + the nav decision, closeout. `/desk` only.
- **Out:** re-skinning Home/Dictation/Meetings (they stay clean cockpits); new backend APIs (the data
  seam exists); the iPad app (separate track); every sprite variant (only the surfaced kinds); a
  SceneKit/WebGL 3D engine (the diorama is 2.5D DOM/CSS + one canvas for motes).

## Exit criteria (evidence required)

- [ ] `/desk` is a warm, lit, atmospheric stage (gradient + radial spotlight + motes), not flat black
      (HS-71-01).
- [ ] Every primitive renders as a floating pixel-art sprite (ported art + stable-hash picker), with a
      detached ground shadow + glow (HS-71-02, HS-71-03).
- [ ] Objects are freely placed (drag, localStorage-persisted) with density-aware auto-layout (HS-71-04).
- [ ] Directories are shelf-zones you drag onto to file (real `PUT`) and dive into with a back control
      (HS-71-05).
- [ ] Qlippy lives in the corner (toggle-honored); created objects get the NEW beat; tap opens an object
      (HS-71-06).
- [ ] The Desk documented; POSITIONING line added; the nav decision implemented; voice guard green
      (HS-71-07).
- [ ] The side-by-side vibe test passes; the full walk proven; route pre-flight green; full suite green;
      `web/public/desk/sprites` committed (HS-71-08).

## Stories

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-71-01 | The room: the warm atmospheric stage | HIGH | **done** (`/desk` gained a fixed `.desk-stage`: DioPal gradient + an animated warm radial spotlight + a canvas of rising dust motes; reduced-motion-safe; content still on top; zero page errors; suite green; see [evidence](./evidence-story-01.md)) | — |
| HS-71-02 | The sprite pipeline: hand-drawn objects on the web | HIGH | **done** (67 pixel-art PNGs copied from `apple/App/` to `web/public/desk/sprites/` + a djb2 stable-hash picker `sprites.js` matching `SpriteStore.swift`, on `window.__deskSprites`; sprite sheet crisp, picker stable + spread; suite green; see [evidence](./evidence-story-02.md)) | — |
| HS-71-03 | Objects that float (the diorama's heartbeat) | HIGH | **done** (`/desk` renders every primitive as a floating pixel-art object — `worldObjects()` + `objStyle` auto-layout + per-object float/glow/detached-shadow via CSS keyframes; card-list preserved under a collapsed "Browse as a list"; 12-object mixed desk proven; zero page errors; suite green; see [evidence](./evidence-story-03.md)) | 01, 02 |
| HS-71-04 | Free placement + the layout store | MED | **done** (drag-to-arrange with unit-space `positions` persisted to `localStorage["hs.diorama.pos"]` (local-only, never synced); `looseHome` density-aware auto-layout for untouched; a "Tidy" reset; objects enlarged; drag persists across reload (Playwright); suite green; see [evidence](./evidence-story-04.md)) | 03 |
| HS-71-05 | Zones as shelves: file and dive | MED | **done** (directories become painted shelf-zones; drag an object onto one to file via real `PUT /api/directories/{id}/members/{pid}`; click to dive in (filter to members) with a back control + empty state; robustness fix for mid-drag layout shift; Playwright drop→1 item, dive→1 member; suite green; see [evidence](./evidence-story-05.md)) | 04 |
| HS-71-06 | In-world Qlippy, the create beat, open-an-object | MED | **todo** | 03 |
| HS-71-07 | Docs + the nav decision (the docs story) | MED | **todo** | 01–06 |
| HS-71-08 | Closeout: the side-by-side, proven | HIGH | **todo** | 01–07 |

Build order (foundation-first): **01 → 02 → 03** (the moment it becomes a world) → **04 → 05** (arrange +
organize) → **06** (life + open) → **07** (docs/nav) → **08** (closeout). 06 can run in parallel after 03.

## Where we are

**2026-07-01 — HS-71-05 done (zones — file + dive).** The desk is a place to organize now. Directories
are excluded from the floating objects and rendered as painted **shelf-zones** (`worldZones` + `zoneStyle`,
laid across the top); dragging an object onto a zone **files** it via the real add-only
`PUT /api/directories/{id}/members/{pid}` (`fileIntoDir`, the same write the iPad uses), the drag handler
now hit-tests the live `.desk-zone` rects at drop; clicking a zone **dives** in (`diveInto` -> `worldObjects`
filters to that zone's members; zones hidden) with a "← All primitives" breadcrumb (`surface`) + an
empty-dive guide. A real robustness bug was found and fixed on the way: a mid-drag layout shift (the "Tidy"
button appearing) desynced the delta-from-start math and the `elementsFromPoint` hit-test - the drag now
tracks the pointer using a FRESH world rect each move, and the drop hit-tests fresh zone rects. Proven with
Playwright: dropping an object on "Q3 release" fired the PUT and the zone read "1 item"; diving in showed
exactly that 1 member with the back control (`05-zones`, `05-dived`). Route pre-flight 2 passed (zero page
errors); full suite 3045 passed, 37 skipped. Next: HS-71-06 (in-world Qlippy + the create beat +
tap-to-open).

**2026-07-01 — HS-71-04 done (free placement).** The desk is hand-arrangeable now. `desk-app.js` gained
`positions` (unit-space `{x,y}` per id) persisted to `localStorage["hs.diorama.pos"]` (local-only, never
synced - matches the iPad contract, no API), `objUnit` (a saved drag position or the `looseHome`
density-aware grid), `startObjDrag` (a pointer drag: delta / stage rect, clamped `0.04..0.96`, persists on
release, a >4px movement threshold so a plain click still opens the object), and `tidyDesk`. `desk.astro`
wires `@pointerdown` on each object + a grab/grabbing cursor (the float freezes while dragging), a
touch-action:none for touch, and a header "Tidy" button (shown only when positions exist). Objects were
enlarged for presence (sprite 76->88, lift 84->96, footprint 112->128) on owner feedback that they read
small. Proven: a Playwright drag saved `{"m0":{"x":0.31,"y":0.29}}` and it persisted across a full reload;
the drag did not open the object. Route pre-flight 2 passed (zero page errors); full suite 3045 passed, 37
skipped. Next: HS-71-05 (zones as shelves - file + dive).

**2026-07-01 — HS-71-03 done (objects that float) — the world moment.** `/desk` stopped being a
document. `desk-app.js` gained `worldObjects()` (flattens `items[kind]` across every kind), `objSprite`
(the HS-71-02 picker), `objGlow` (per-kind tint), and `objStyle` (a loose density-aware auto-layout +
per-object jitter that sets `--phase`/`--tilt`/`--oscale`/`--k`). `desk.astro` renders each primitive as a
`.desk-obj` that floats (`desk-bob` CSS keyframes, delayed by `--phase` so they don't bob in sync) with a
pixel-crisp sprite, a per-kind glow pool, and a **detached ground shadow** that stays on the floor and
softens/narrows as the object lifts (the counter-animated "floating above a surface" cue) — all
`<style is:global>` since Alpine injects them. The old grouped card-list + authoring UI is preserved under
a collapsed "Browse as a list" `<details>` beneath the world (nothing lost; the world is the star).
Reduced-motion freezes the float. Performance stays cheap — pure CSS keyframes with a per-object phase, no
rAF over N objects. Proven with a 12-object mixed desk (4 meetings + 3 notes + 2 KBs + 2 agents + 1
directory, seeded via the real `/api/*` POSTs): cassettes, notepads, crystals, avatars, and paper floating
on the warm room (`03-world`). Route pre-flight 2 passed (zero page errors); full suite 3045 passed, 37
skipped. Next: HS-71-04 (free drag-to-arrange + the density-aware `looseHome` layout + persistence).

**2026-07-01 — HS-71-02 done (the sprite pipeline).** The iPad's pixel-art primitive sprites are on the
web. 67 PNGs (128x128 RGBA) copied verbatim from `apple/App/` into `web/public/desk/sprites/` (cassette 17
/ note 16 / crystal 16 / cartridge / agent_o 16 / paper) with a provenance README. `sprites.js` is the
port of `SpriteStore.swift`: `stableHash` is djb2 with an **exact 64-bit two's-complement wrap** (BigInt,
so it matches Swift's `h &* 33 &+ byte` + `abs()` where a JS Number would lose precision), the `VARIANTS`
pools mirror `DeskSprites.variants` (+ avatar/paper/cartridge art for the kinds the iPad draws as SF
Symbols), and `spriteUrl` uses Astro `BASE_URL` (`/_built/desk/sprites/...`, matching how `/_built/qlippy/*`
serves). Wired onto `window.__deskSprites` for the `?raw`-loaded `desk-app.js`. Proven: a sprite sheet
renders every kind crisp and pixel-perfect (`02-sprite-sheet`), and the in-page picker check shows stable
per-id + 8/8 distinct across the pooled kinds. Not on the desk yet (still the card-list) - HS-71-03 floats
them. Route pre-flight 2 passed; full suite 3045 passed, 37 skipped. Next: HS-71-03 (objects that float).

**2026-07-01 — HS-71-01 done (the room).** `/desk` stopped loading as flat black. A full-bleed fixed
`.desk-stage` (`z-index: -1`, behind the content) now holds the diorama atmosphere: the DioPal vertical
gradient (#0B0D12 → #16111F → #090A0E), an animated warm radial spotlight (an orange core high at
`50% 34%` + a violet undertone + a low warm floor, `plus-lighter`, a 7s opacity/rise pulse — the port of
the iPad's `sin`-driven radial), and a `<canvas>` of ~18 rising dust motes on one cheap rAF loop
(the DioMotes port). Reduced-motion freezes the spotlight and motes. The existing card-list still renders
on top unchanged — content becomes floating sprites in HS-71-03, which will reveal the room across the
whole stage. It is static Astro markup, so scoped CSS applies (no `is:global` needed until the objects
are Alpine-injected). Screenshot-proven (`01-room-atmosphere`); route pre-flight 2 passed (zero page
errors — the new canvas + script are clean); full suite 3045 passed, 37 skipped. Next: HS-71-02 (the
sprite pipeline).

**2026-07-01 — opened + scaffolded.** Authored from the owner's "nowhere near the look and feel of the
iOS app" + the side-by-side (iPad diorama vs. web flat card-list) + the owner's choice to port the
diorama. Grounded by a technical map (the scaffold Explore) that traced the iPad diorama
(`DeskDioramaStage.swift`), the web `/desk` data seam (`desk.astro` + `desk-app.js`, already loading every
kind from `/api/*`), the sprite art (committed in `apple/App/`, only Qlippy on web so far), and the
local-only geometry contract. The headline finding: the data layer is done, so this is a rendering change
plus one sprite-asset copy. Next: an agent starts HS-71-01 (the room) on branch `phase-71-desk-as-world`
under the PMO gate.
