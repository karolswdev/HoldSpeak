# Phase 71 — Agent Brief (read this first)

**Phase 71 — The Desk, as a World (the web diorama).** Opened on owner
direction after Phase 70 shipped: the web is now legible and consistent, but it
still *feels* like a document while the iPad *feels* like a world. The owner,
shown the two "Desks" side by side, chose the full fix: **port the iPad DeskOS
2.5D diorama to the web.**

## 0. Mission

Make the web `/desk` feel like the iPad desk: a warm, atmospheric, spatial
world where every primitive is a floating hand-drawn object you arrange, file,
and dive into. Not a themed card grid. A world.

The good news, established by the Phase-71 scaffold's technical map: **this is
primarily a rendering change, not new plumbing.** The web `/desk` already loads
every primitive kind live from the same `/api/*` endpoints the iPad's
`HTTPDesktopClient` uses. The data layer exists; the world does not.

## 1. The one thing you must not get wrong

**It has to feel like a world, not a webpage with nicer icons.** The acceptance
test is the side-by-side (HS-71-08): at a glance of the *vibe* — the warm
lit atmosphere, objects floating with detached shadows, depth — a stranger
cannot immediately tell which screen is the iPad and which is the web. If the
result still reads as "a dashboard with a gradient and some sprites," it failed,
no matter how clean the diff. Atmosphere + floating sprites + depth are the
irreducible core; ship them first (HS-71-01 → 03) and keep checking the vibe
against the real iPad screenshot.

## 2. What the iPad diorama actually is (the target, traced from Swift)

Source: `apple/App/MeetingCapture/DeskDioramaStage.swift` (pure SwiftUI 2.5D).
The ingredients that make it a world:

- **Warm atmosphere** — a full-bleed vertical gradient (`DioPal`: `bgTop
  #0B0D12` → `bgMid #16111F` → `bgBot #090A0E`) under an **animated warm radial
  spotlight** centered high (`0.5, 0.4`), tinted by the active zone/selection,
  pulsing via `sin(t*1.2)`, `.plusLighter` blend. Plus **rising dust motes**
  (`DioMotes`, 16 slow translucent specks). Accent orange `#FF6B35`.
- **Objects that float** — each primitive is a **bundled pixel-art PNG sprite**
  (`DeskSprite`, `.interpolation(.none)`), not a vector icon. Per object
  (`DioHeroVisual`): vertical **bob** (`sin(t*0.9)`) + **breathe** scale + slow
  **tilt**; a **detached soft ground shadow** (a blurred ellipse that separates
  from the object as it bobs — this sells "floating above a surface"); a per-kind
  **glow pool** (radial halo, accent when hot); a **drop shadow** on the sprite.
- **Free placement + density-aware layout** — objects live at a unit-space
  position `positions[id]` (0..1), drag-to-arrange, persisted per-device
  (`hs.diorama.pos`). Untouched objects fall to an auto layout (`looseHome`) that
  **spreads as the desk fills** (more items → more columns) and **shrinks
  objects to a usability floor** (`densityScale`).
- **Zones as shelves** — directories render as low-profile painted shelf-trays;
  you **file** a primitive by dragging it onto a zone, and **dive** into a zone
  (a camera "level" change with a spring transition) to see its contents.
- **A living mascot** — Qlippy (`DioCompanion`) sits in the corner
  (`~0.9, 0.86`) with sway/bob/hop + its own ground shadow. Decorative.

## 3. The seam you build on (traced from the web)

- **Page**: `web/src/pages/desk.astro` (Alpine). It loads the factory as a raw
  string: `import factorySource from "../scripts/desk-app.js?raw"` +
  `new Function(...)` + `Alpine.data("DeskApp", fn())` + `Alpine.start()`. The
  root is `<div class="desk" x-data="DeskApp()" x-init="init()">`.
- **The data is already live.** `desk-app.js` `loadAll()` pulls every kind from
  `/api/meetings`, `/api/sync/pull` (artifacts), `/api/notes`, `/api/agents`,
  `/api/kbs`, `/api/directories`, `/api/chains`, `/api/workflows`,
  `/api/profiles`, `/api/companion/status`, `/api/setup/status`, and normalizes
  each into `this.items[kind]` = `[{ kind, id, title, … }]`. **No new read API is
  required.**
- **Kinds** (`web/src/lib/primitives.ts` + `desk.astro` `META`/`DESK_GROUPS`):
  `meeting, artifact, note, agent, chain, workflow, directory, kb, coder`
  (+ `game`). The web `directory` == the iPad `zone`.
- **Geometry is local-only** on both surfaces (the iPad keeps `positions`/zone
  geometry in `@AppStorage`, deliberately NOT synced; directories carry only
  identity/nesting/membership). The web keeps its positions in `localStorage`.
  **No geometry API. Do not add one.**

## 4. The sprite art (the one real asset task)

The primitive PNGs are committed in `apple/App/` but only **Qlippy** is under
`web/public/` today (`web/public/qlippy/`, web-ready). A story must **copy the
needed primitive PNGs into `web/public/desk/sprites/`** (per the kind→sprite map
in `SpriteStore.swift`: `cassette*.png` meetings, `note*.png` notes,
`crystal*.png` KBs, `cartridge.png` models, `agent_*` avatars, `game_*` covers)
and add a JS **stable-hash sprite picker** (djb2, matching `SpriteStore.stableHash`
so a given id maps to the same variant the iPad would pick). `web/public/` IS
committed (unlike the gitignored `holdspeak/static/_built/`). The PNGs are plain
rasters; nothing about them is iOS-specific.

## 5. Rules (the standing set)

PMO gate (fresh `.tmp/CONTRACT.md`, ≥7 `[x]`, one story-flip per commit with its
`evidence-story-NN.md`); cadence per shipping commit (story header + this
`current-phase-status.md` + the project `README.md` + POSITIONING when touched);
branch `phase-71-desk-as-world`, one PR per slice, merged on green CI; full suite
via `uv run pytest -q --ignore=tests/e2e/test_metal.py`. The `Co-Authored-By` +
`Claude-Session` footer is the current commit convention.

## 6. Gotchas that WILL bite

- **Astro scoped CSS never reaches JS/`innerHTML`-injected DOM.** The sprite
  objects are Alpine-rendered, so their CSS must be `<style is:global>`.
  Screenshot-verify; a class in the bundle is not proof it paints.
- **The built bundle (`holdspeak/static/_built/`) is GITIGNORED.** Edit
  `web/src` + `web/public`, then `cd web && npm run build`; commit source +
  public only.
- **`desk.astro` loads its factory via `?raw` + `new Function`** (not ES import).
  Keep that pattern; `desk-app.js` is a plain `function DeskApp(){…}` (no export).
- **Performance: many floating animated objects.** Do NOT run a per-frame rAF
  loop over N sprites. Use **CSS keyframe animations** with a per-object phase
  offset via a CSS custom property (`--phase`), so the GPU animates float/glow
  and the JS only sets positions on drag. `image-rendering: pixelated` for the
  crisp pixel look.
- **Match the iPad math + palette** (DioPal hexes; bob `sin(t*0.9)`; the detached
  shadow offset; the glow radial) so the two surfaces read as the same world.
- **A running hub picks a RANDOM free port**; find it via `lsof -nP -iTCP
  -sTCP:LISTEN | grep -i python`. Seed a temp DB in screenshot scripts (the
  `MeetingWebServer` + Playwright pattern the Phase-70 shot scripts use).

## 7. What this phase is NOT

- Not a re-skin of Home / Dictation / Meetings. Owner call: those stay **clean,
  fast cockpits**. Only `/desk` becomes the world. (Whether the diorama gets
  promoted out of the Studio tier in the nav is an explicit HS-71-07 question,
  not assumed.)
- Not new backend APIs. The data seam exists; this is rendering + one asset copy.
- Not a change to the iPad app (separate track). This ports its *look*, not its
  code.
- Not porting every sprite variant — port the kinds the web desk surfaces.
- Not a SceneKit/WebGL 3D engine. The iPad diorama is 2.5D SwiftUI (CSS-equivalent
  transforms + gradients + shadows). Build it with DOM/CSS, same as the iPad
  builds it with SwiftUI layers. Reach for `<canvas>` only for the dust motes.

## 8. Definition of done (phase-level)

- `/desk` is a warm, lit, atmospheric spatial stage (gradient + radial spotlight
  + motes), not flat black.
- Every primitive renders as a **floating pixel-art sprite** with a detached
  ground shadow + glow, from the ported art + the stable-hash picker.
- Objects are **freely placed** (drag to arrange, localStorage-persisted) with
  density-aware auto-layout for untouched ones.
- **Directories are shelf-zones** you can drag an object onto to file it, and
  **dive into** to see contents, with a way back.
- **Qlippy lives in the corner**; created objects get the NEW beat; tapping an
  object opens it.
- The side-by-side vibe test passes (HS-71-08): it reads as the same world as the
  iPad, not a themed dashboard.
- Full suite green; no new backend API; `web/public` sprites committed, `_built`
  never committed.
