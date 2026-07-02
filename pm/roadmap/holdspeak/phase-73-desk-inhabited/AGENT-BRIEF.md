# Phase 73 — Agent Brief (read this first)

**Phase 73 — The Desk, Inhabited (on the React foundation).** Opened
2026-07-02 on owner direction; **re-scaffolded the same day** on two further
owner decisions, before any story executed:

1. **The Desk is the main surface.** Owner, verbatim: "the desk is
   absolutely the main surface I expect users to use when they do run
   HoldSpeak on their computers — not a shadow of a doubt here." The Desk
   becomes the web app's front door (`/`). This formally supersedes
   Phase 70's four-door IA by owner decision.
2. **React + Vite is the stack for interactive surfaces.** The Alpine
   `?raw` + `new Function` pattern is retired for the desk and banned for
   new surfaces. Astro remains the thin static shell for document-shaped
   pages. This phase builds the Desk as a React island inside the existing
   Astro build — one build pipeline, nothing changes about FastAPI serving
   `/_built`.

The original diagnosis stands: the iPad desk is the owner's proudest
surface; the Phase-71 web port is "a primitive copy, an uninviting mess"
because it ported the **renderer, not the inhabitation** — every verb
(create, edit, open, record, run) still lives in the old page paradigm.
This phase ports the inhabitation, on a foundation that can carry it.

## 0. Mission

Make `/` a place you *work*: arrive on the Desk → create a note in place →
edit it in place → record a meeting from the orb → watch it materialize as
an object → open its pull-out → run an agent from the rail → file into a
zone → dive → back. **Zero route changes across the whole walk** except the
explicit "Open full" escape hatch. If any step ejects the user to a form
drawer, an admin list, or another page, the phase failed regardless of how
the hero screenshot looks.

## 1. The stack (decided — do not relitigate)

- **React 18+ + TypeScript**, compiled by the existing Astro/Vite build via
  `@astrojs/react`; the desk mounts as a single island
  (`<DeskApp client:only="react" />`) on an otherwise-empty page. No SSR,
  no node at runtime — the output stays a static bundle FastAPI serves.
- **State:** Zustand (one store: items, positions, zones, dive, pull-out,
  editor, orb, rail). **Motion:** the `motion` package (Framer Motion) for
  springs — the desk's float/materialize/pull-out choreography. **Gestures:**
  `@use-gesture/react` for drag (or plain pointer events where simpler).
- **Types:** `web/src/lib/primitives.ts` is the contract layer — the React
  API client imports it; do not fork the shapes (Phase 72's HS-72-01
  schemas will lock them).
- **CSS:** the Signal tokens (`web/src/styles/tokens.css`) are plain custom
  properties — reuse them as-is. Component styles are plain imported CSS or
  CSS modules; the Astro `is:global` tax does not exist inside the island.
- **Live events:** subscribe to the `hs-*` DOM events `runtime-bus.js`
  dispatches on `window` (a `useRuntimeBus` hook). This seam is stable
  across Phase 72's HS-72-08 socket refactor — do not open a socket in the
  island.
- **Standing rule (record in docs, HS-73-09):** new interactive surfaces
  are React; document pages stay Astro; **no new Alpine, ever**. `/history`
  and `/live` migrate in a later phase (HS-72-07 was cut for this reason).

## 2. The reference implementation (the iPad, traced)

The target grammar lives in `apple/App/MeetingCapture/DeskDioramaStage.swift`
(`DioStage`). The pieces this phase ports, by name:

- **Zero chrome** — gear, small create chips, one whispered hint. Reference
  screenshot: `pm/roadmap/holdspeak-mobile/phase-20-one-app-every-size/screenshots/2001-ipad-wide.png`.
- **`DioInlineNoteCard` / `DioInlineKBCard`** — in-world editors: the object
  IS the editor; New Note creates the record instantly, then you edit in
  place (the owner's standing rule from the 2026-06-27 device-gap
  punch-list; no dim-scrim modals, ever).
- **`DioPullout`** (~line 1221) — tap an object, a drawer slides out on the
  stage; a meeting's pull-out groups derivatives by lineage
  (`provenance.sourceCardId` / `source == title`) — the meeting drawer
  (PR #196).
- **Zones as landmarks** — painted trays, member thumbnails, counts, tint
  (`ZoneRec` ~305); inline hint when empty.
- **`DioAmbientRecorder`** (~1915) + the Record orb — the primary verb
  bottom-center IN the world; a finished recording becomes an object.
- **The agent rail** (`DeskAgents.swift`) — personas run from the world.

## 3. What exists to port from (the Alpine desk, verified inventory)

The legacy surface is `web/src/pages/desk.astro` (1,732 lines) +
`web/src/scripts/desk-app.js` (1,472 lines, the `DeskApp()` Alpine factory).
It is the **behavioral spec** for the world layer — port semantics, not
code. The load-bearing pieces, with line numbers:

- Data: `loadAll()` (:464) pulls every kind — `/api/meetings`,
  `/api/sync/pull` (artifacts), `/api/notes`, `/api/agents`, `/api/kbs`,
  `/api/directories`, `/api/chains`, `/api/workflows`, `/api/profiles`,
  `/api/companion/status` — into `items[kind]`. Per-kind `fromWire*`
  normalizers at :556/:582/:648/:676/:782/:806.
- World: `worldObjects()` (:219), `objSprite/objGlow/objStyle` (:250–286),
  `looseHome` density layout, per-object float phase.
- Placement: `positions` in `localStorage["hs.diorama.pos"]` (:287–295,
  local-only, NEVER synced — the Primitive Framework layout rule),
  `startObjDrag` (:296, unit-space, 0.04..0.96 clamp, >4px tap/drag
  threshold), `tidyDesk` (:347).
- Zones: `worldZones` (:236), `zoneStyle` (:355), `fileIntoDir` (:364 —
  real `PUT /api/directories/{id}/members/{pid}`), `diveInto/surface`
  (:375/379), membership maps `directoriesFor/memberOf` (:691/752).
- Beats: `markNew/isNew` (:393/398); `openObject` (:400) — the bounce-out
  you are killing; lineage helpers `lineage/hasLineage` (:853/880) — the
  pull-out's grouping logic, ready to port.
- Trust: `egressBadge()` (:152), `profileEgress` (:618).
- Sprites: `web/public/desk/sprites/` (67 PNGs) + `sprites.js` — port the
  djb2 `stableHash` to TS **with the BigInt 64-bit two's-complement wrap**
  (a plain JS Number loses precision and breaks sprite stability; this was
  hard-won in HS-71-02).

## 4. Standing gotchas

- `holdspeak/static/_built/` is **gitignored**: edit `web/src`, verify with
  `cd web && npm run build`, commit source only.
- Screenshot-verify every story — a class in the bundle is not proof it
  applies. (The React island removes the `is:global` trap, but the shell
  pages around it keep it.)
- The suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Route
  pre-flight (`tests/e2e/test_route_preflight.py`) must stay green — and it
  must be UPDATED when `/` changes meaning (HS-73-02).
- The first-run guard currently lives inline on `index.astro` (redirect to
  `/welcome` when `first_run`, `/setup` when blocked) — it MUST survive the
  desk takeover of `/` (HS-73-02).
- PMO gate: `.tmp/CONTRACT.md` fresh per commit; one story per PR; evidence
  ships with the done-flip.
- Owner rules, mechanical by HS-73-09: **no modals** (no `role="dialog"`/
  `aria-modal` in the desk tree), **no prose** (labels, one whispered hint,
  the egress badge instead of privacy sentences).

## 5. Build order

**01** (the React foundation: island + data layer + the world at render
parity) → **02** (the arrival: desk is `/`, immersive chrome, first-run
guard, guiding empty state) → **03** (create in-world) / **04** (the
pull-out) → **05** (zones + file/dive complete) → **06** (the Record orb) /
**07** (the agent rail) in parallel → **08** (the cutover: the Alpine desk
dies behind a zero-loss verb inventory) → **09** (docs + the locks) →
**10** (the inhabited walk).
