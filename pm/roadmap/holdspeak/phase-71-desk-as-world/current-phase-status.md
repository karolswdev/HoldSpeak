# Phase 71 — The Desk, as a World (the web diorama)

**Status:** SCAFFOLDED (0/8) — 2026-07-01. Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

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
| HS-71-01 | The room: the warm atmospheric stage | HIGH | **todo** | — |
| HS-71-02 | The sprite pipeline: hand-drawn objects on the web | HIGH | **todo** | — |
| HS-71-03 | Objects that float (the diorama's heartbeat) | HIGH | **todo** | 01, 02 |
| HS-71-04 | Free placement + the layout store | MED | **todo** | 03 |
| HS-71-05 | Zones as shelves: file and dive | MED | **todo** | 04 |
| HS-71-06 | In-world Qlippy, the create beat, open-an-object | MED | **todo** | 03 |
| HS-71-07 | Docs + the nav decision (the docs story) | MED | **todo** | 01–06 |
| HS-71-08 | Closeout: the side-by-side, proven | HIGH | **todo** | 01–07 |

Build order (foundation-first): **01 → 02 → 03** (the moment it becomes a world) → **04 → 05** (arrange +
organize) → **06** (life + open) → **07** (docs/nav) → **08** (closeout). 06 can run in parallel after 03.

## Where we are

**2026-07-01 — opened + scaffolded.** Authored from the owner's "nowhere near the look and feel of the
iOS app" + the side-by-side (iPad diorama vs. web flat card-list) + the owner's choice to port the
diorama. Grounded by a technical map (the scaffold Explore) that traced the iPad diorama
(`DeskDioramaStage.swift`), the web `/desk` data seam (`desk.astro` + `desk-app.js`, already loading every
kind from `/api/*`), the sprite art (committed in `apple/App/`, only Qlippy on web so far), and the
local-only geometry contract. The headline finding: the data layer is done, so this is a rendering change
plus one sprite-asset copy. Next: an agent starts HS-71-01 (the room) on branch `phase-71-desk-as-world`
under the PMO gate.
