# Phase 73 — Agent Brief (read this first)

**Phase 73 — The Desk, Inhabited.** Opened on owner direction 2026-07-02: the
iPad desk is the surface the owner is proudest of; the web `/desk` is, in the
owner's words, "a primitive copy, an uninviting mess." A usability scan
confirmed why with precision: **Phase 71 ported the renderer, not the
inhabitation.** The atmosphere, sprites, float, drag, and file/dive made it
to the web — but every *verb* (create, edit, open, record, run) still lives
in the old page paradigm, stacked on the same route. The web desk is a page
wearing a world costume.

## 0. Mission

Make the web `/desk` a place you *work*, not a place you *look at*. The bar
is behavioral, not visual: **every verb of the daily walk happens inside the
world, with zero route changes** except the explicit "Open full" escape
hatch. Arrive → create a note in place → edit it in place → record a meeting
from the orb → watch it materialize as an object → open its pull-out → run
an agent from the rail → file into a zone → dive → back. If any step of that
walk ejects the user to a form drawer, a scroll-down admin list, or another
page, the phase has failed regardless of how the hero screenshot looks.

## 1. The three owner rules this phase exists to enforce (non-negotiable)

These are standing, app-wide rules that were enforced on the iPad and never
applied to the Phase-71 web port. Phase 73 applies them and then **locks them
with guards** so they cannot return:

1. **No modals.** Create/edit happens in-world, in place. The current
   `role="dialog" aria-modal="true"` form drawers (`desk.astro:488+`) are the
   exact pattern the owner banned repeatedly on iOS.
2. **No prose in the UI.** Labels, not manuals; no selling, no reassurance,
   no how-to sentences. The current header lead ("Every primitive,
   first-class on the web — authored here, living on your desktop hub…",
   `desk.astro:53`) and microcopy like "Saves to `POST /api/notes` on your
   desktop hub" are banned copy. The iPad's ceiling is one whispered hint:
   "drag a meeting onto a zone · tap to open".
3. **Egress is a badge, not a sentence.** The `egressBadge()` helper already
   exists in `desk-app.js:152`; anything that narrates privacy in words dies.

## 2. The reference implementation (the iPad, traced)

The target grammar lives in `apple/App/MeetingCapture/DeskDioramaStage.swift`
(`DioStage`, ~5,400 lines). The pieces this phase ports, by name:

- **Zero chrome** — no header stack; a settings gear, small create chips
  (`New Note` / `New KB` / `New Zone`), a one-line hint under the wordmark.
  Reference screenshot: `pm/roadmap/holdspeak-mobile/phase-20-one-app-every-size/screenshots/2001-ipad-wide.png`.
- **`DioInlineNoteCard` / `DioInlineKBCard`** — in-world editors: the object
  IS the editor; no dim scrim, no form sheet. "New Note" creates the record
  instantly, then you edit in place (the owner's "New Note must actually
  create a card instantly" rule from the 2026-06-27 device-gap punch-list).
- **`DioPullout`** (~line 1221) — tap an object, a drawer slides out on the
  stage. A meeting's pull-out groups its derivatives (summary / actions /
  artifacts) by lineage (`provenance.sourceCardId` / `source == title`) —
  the "meeting drawer" (PR #196, view-layer grouping, owner's explicit
  choice).
- **Zones as landmarks** — painted trays with member sprite thumbnails +
  counts + tint (`ZoneRec` ~line 305); an inline hint when empty.
- **`DioAmbientRecorder`** (~line 1915) + the Record orb — the product's
  primary verb lives bottom-center IN the world; a finished recording
  becomes an object in front of you.
- **The agent rail** — right-edge avatar rail (`DeskAgents.swift`); personas
  run from the world, results land in the world.

## 3. The web seam (what exists today, exactly)

- **Page:** `web/src/pages/desk.astro` (1,732 lines). Structure: AppLayout
  wrapper (line 40) → `.desk-stage` atmosphere (HS-71-01) → `.desk-head`
  header stack (~49–83: eyebrow, H1, the banned lead paragraph, stat
  counter, New note / New agent / Tidy / Refresh buttons) → `.hub-bar`
  status pills (~85+) → the world → **"Browse as a list"** `<details>`
  (lines 158–429: per-kind card sections with `openCreate(kind)` add
  buttons, "Move to…" `openFile(kind,item)`, `openRun(item,'agent'|'chain'
  |'workflow')` run buttons, empty-state "Create the first …" links) →
  create/run/file **drawers** (`role="dialog"`, lines 488+).
- **App:** `web/src/scripts/desk-app.js` (1,472 lines), the Alpine
  `DeskApp()` factory loaded via `?raw` + `new Function` (Astro drops
  non-prop attributes on components, so Alpine pages load factories as raw
  strings — keep this pattern). The methods you will build on:
  `worldObjects()` / `worldZones()` (219/236), `objSprite/objGlow/objStyle`
  (250–286), positions + `startObjDrag` + `tidyDesk` (287–354,
  `localStorage["hs.diorama.pos"]`, local-only, never synced), `zoneStyle`
  (355), `fileIntoDir` (364, real `PUT /api/directories/{id}/members/{pid}`),
  `diveInto/surface` (375/379), `markNew/isNew` create beat (393/398),
  `openObject` (400 — currently meetings → `/history?meeting=id`, others
  reveal the list card: **this is the bounce-out you are killing**),
  `loadAll()` (464, pulls every kind from `/api/*`), `lineage(sources)` /
  `hasLineage` (853/880 — the grouping logic the pull-out needs already
  half-exists), `egressBadge()` (152), `refreshCoders()` (885).
- **Sprites:** `web/public/desk/sprites/` (67 PNGs) + `sprites.js` djb2
  picker on `window.__deskSprites`.
- **Already-built motion/widgets to reuse (Phase 69):** the `hs-materialize`
  motion, the generation theater (orb + constellation), the premium confirm
  sheet, the Queue HUD, the egress badge, the reactive `Waveform` — all
  mounted by `web/src/layouts/AppLayout.astro` (~lines 80–119).
- **Live plumbing:** `POST /api/meeting/start|stop` + `GET /api/state`
  (`holdspeak/web/routes/core.py`) — the exact calls `/live`'s
  `dashboard-app.js` makes; `runtime-bus.js` already opens a `/ws` on every
  page and re-dispatches frames as `hs-*` DOM events.

## 4. Standing gotchas (each has burned a phase before)

- **Astro scoped CSS never reaches Alpine-injected DOM.** Everything the
  factory renders needs `<style is:global>`. A class present in the built
  bundle is NOT proof it applies — screenshot-verify every story.
- `holdspeak/static/_built/` is **gitignored**: edit `web/src`, verify with
  `cd web && npm run build`, commit source only.
- Never use escaped quotes inside Alpine attributes (the Phase-62
  `welcome.astro` SyntaxError).
- The suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`. Route
  pre-flight (`tests/e2e/test_route_preflight.py`) must stay green — it
  catches dead-on-arrival pages.
- PMO gate: `.tmp/CONTRACT.md` fresh per commit; one story per PR; evidence
  ships with the done-flip.

## 5. Coordination with Phase 72 (One Spine, open in parallel)

- **HS-72-08 (one live bus)** makes the Record orb cleaner. Do not block on
  it: `runtime-bus.js` already runs on every page today — subscribe to its
  `hs-*` events as-is; if 72-08 lands first, nothing changes for you.
- **HS-72-03** renames `/api/companion/*` → `/api/coders/*`
  (`desk-app.js:885 refreshCoders` is a caller). Whichever phase lands
  second rebases a one-line path; both branches stack on `phase-72-one-spine`.
- **Phase 72's "desk.astro decomposition" watch item is absorbed here**:
  HS-73-01 rebuilds the page as `components/desk/` partials, so by closeout
  the monolith is gone as a side effect of the UX work.

## 6. Build order

**01** (full-bleed — half the felt gap, mostly deletion) → **02** (create
in-world) and **03** (the pull-out) in either order → **04** (delete the
appendix — only after 02+03 cover every verb) → **05** (zones) and **06**
(the Record orb) and **07** (the agent rail) in parallel → **08** (docs +
the guards) → **09** (the inhabited walk).
