# Phase 73 — The Desk, Inhabited

**Status:** open — scaffolded 2026-07-02, 0/9.

**Last updated:** 2026-07-02 (**opened + scaffolded** on owner direction: the
web `/desk` is "a primitive copy, an uninviting mess" next to the iPad desk
the owner is proud of. A usability scan of both surfaces — the committed hero
screenshots side by side plus the `/desk` source — produced the diagnosis and
the nine stories. Branch `phase-73-desk-inhabited`, stacked on
`phase-72-one-spine`.)

## The thesis

Phase 71 passed its closeout "vibe test" honestly — at a static glance the
web desk reads as the iPad's world. But usability is what happens when you
*touch* it, and every touch ejects the user from the world:

- **The world doesn't own the screen.** `/desk` opens with a document header
  stack (top nav → "DeskOS · Primitive Framework" eyebrow → H1 → a
  three-line selling paragraph → a stat counter → a five-button toolbar → a
  hub-status pill bar) before the stage starts. The iPad gives the world
  100% of the screen with a gear, three chips, an agent rail, a Record orb,
  and one whispered hint.
- **The banned patterns came back.** The header lead (`desk.astro:53`) is
  exactly the prose the no-prose-in-UI rule kills; creation is a
  `role="dialog" aria-modal="true"` form drawer (`desk.astro:488+`) — the
  dim-scrim modal pattern the owner banned on iOS — with "Saves to
  `POST /api/notes`" as microcopy.
- **Creation happens outside the world** (modal form → submit → only then
  the NEW beat), **editing doesn't exist in the world** at all, and **open
  is a bounce-out**: `openObject` (`desk-app.js:400`) sends meetings to
  `/history?meeting=id` and reveals every other kind's card inside "Browse
  as a list" — the collapsed `<details>` (`desk.astro:158–429`) where the
  entire pre-Phase-71 admin page still lives under the world. Two paradigms
  on one route; the functional one is the ugly one.
- **Zones are flat rectangles** with a text count, not the iPad's painted
  member-thumbnail trays.
- **The world has no live verb.** The iPad desk's center of gravity is the
  Record orb; the web desk can do nothing live — recording lives on `/live`,
  a different door.

Phase 73 ports the inhabitation: in-world create/edit/open, zones as
landmarks, the Record orb, the agent rail — then deletes the legacy appendix
and locks the owner rules with guards. Nearly every ingredient already
exists (the pull-out grammar and inline editors on the iPad as reference;
the materialize motion, generation theater, confirm sheet, egress badge,
waveform, and live-start plumbing on the web from Phases 69/70) — **this is
a composition phase, not an invention phase.**

## Scope

- **In:** the nine stories below. Web-only: `web/src/pages/desk.astro`
  (rebuilt as `components/desk/` partials), `web/src/scripts/desk-app.js`
  (+ new `scripts/desk/` modules), `web/src/layouts/AppLayout.astro` (an
  immersive-chrome variant), guards under `tests/`, docs (`docs/WEB_DESK.md`,
  POSITIONING's desk paragraph). No schema changes; at most additive,
  read-only use of existing `/api/*` routes.
- **Out:** the iPad app (it is the reference, not a target); new backend
  routes (every verb maps to an existing endpoint — the stories name each
  one); browser-side microphone capture (the web Record orb starts the
  hub's recorder via `POST /api/meeting/start`, the `/live` pattern — a
  browser-mic path would be new plumbing and a new egress story);
  `/companion`'s coder board (Phase 72 renames it; the desk rail is
  personas only — `agent` ≠ `coder`); the Workbench graph (HSM 22);
  re-skinning any other page.

## Exit criteria (evidence required)

- [ ] `/desk` is full-bleed: no header stack, no pill bar; chrome is a
      floating minimal cluster + auto-hiding nav; the world owns the
      viewport (HS-73-01).
- [ ] Note/KB/agent/zone creation happens in-world, instantly, edited in
      place; the `role="dialog"` drawers are deleted (HS-73-02).
- [ ] Tapping any object opens an in-world pull-out (meetings: lineage-
      grouped derivatives); no route change except the explicit "Open full"
      (HS-73-03).
- [ ] The "Browse as a list" appendix is gone with a zero-loss verb
      inventory proven (HS-73-04).
- [ ] Zones are painted trays with member thumbnails, counts, tint, and an
      empty hint; dive/back is a camera transition (HS-73-05).
- [ ] The Record orb starts/stops the hub recorder from the desk; the
      finished meeting materializes as an object; the orb reflects
      externally-started meetings (HS-73-06).
- [ ] The agent rail runs a persona from the world with the generation
      theater; the result lands in the world (HS-73-07).
- [ ] Docs rewritten; the no-prose and no-modal locks extended to `/desk`
      and proven to fail on the old copy (HS-73-08).
- [ ] The full inhabited walk passes with zero route changes (Playwright,
      committed); the side-by-side re-shot against the iPad; suite + route
      pre-flight green (HS-73-09).

## Stories

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-73-01 | Full-bleed: the world owns the screen | HIGH | todo | — |
| HS-73-02 | Create in-world (kill the modals) | HIGH | todo | 01 |
| HS-73-03 | Open in-world: the pull-out | HIGH | todo | 01 |
| HS-73-04 | Delete the appendix (one paradigm) | MED | todo | 02, 03 |
| HS-73-05 | Zones as landmarks | MED | todo | 01 |
| HS-73-06 | The Record orb (the live verb) | HIGH | todo | 01 |
| HS-73-07 | The agent rail: run from the world | MED | todo | 01, 03 |
| HS-73-08 | Docs + the locks (the docs story) | MED | todo | 01–07 |
| HS-73-09 | Closeout: the inhabited walk | HIGH | todo | 01–08 |

Build order: **01** (half the felt gap, mostly deletion) → **02 / 03** →
**04** (only after 02+03 cover every appendix verb) → **05 / 06 / 07** in
parallel → **08** → **09**.

## Where we are

**2026-07-02 — opened + scaffolded.** Authored from the usability scan
(the side-by-side of `phase-20/screenshots/2001-ipad-wide.png` vs
`phase-71/screenshots/08-web-desk-hero.png`, plus a symbol-level inventory
of `desk.astro` / `desk-app.js`). The scan's finding, owner-confirmed:
Phase 71 ported the renderer, not the inhabitation — the world layer landed,
every verb still lives in the old page paradigm (modal create drawers, the
"Browse as a list" admin appendix at `desk.astro:158–429`, `openObject`
bouncing to `/history`), and two of the owner's standing UI rules (no
modals, no prose) are violated on this surface. Nine stories authored with
exact seams and symbols. Next: an agent starts HS-73-01 on branch
`phase-73-desk-inhabited` under the PMO gate.

## Active risks

| Risk | Mitigation | Stop signal |
|------|------------|-------------|
| The rebuild unstyles Alpine-rendered DOM (the standing Astro gotcha) | All world CSS `<style is:global>`; screenshot-verify every story, never trust the bundle | A class present in `_built` that does not visually apply in the story screenshot |
| Deleting the appendix loses a verb (delete, edit-field parity, run, move-to) | HS-73-04's zero-loss inventory: every appendix control mapped to its in-world home BEFORE deletion; anything unmappable relocates to a `/studio` page, never silently dropped | Any appendix `@click` handler with no in-world or `/studio` equivalent at HS-73-04 review |
| The Record orb double-starts or lies about state | Orb state derives from `GET /api/state` + `hs-*` frames, never local assumption; disable while a meeting is live elsewhere; reuse `/live`'s start/stop calls verbatim | Two concurrent `POST /api/meeting/start` calls observed, or the orb shows idle while `/api/state` reports recording |
| Auto-hiding nav breaks discoverability or a11y | Nav reappears on mouse-to-top, keyboard focus, and touch; route pre-flight + an axe/keyboard pass in HS-73-01's proof | A keyboard-only user cannot leave `/desk` |
| Parallel-phase collision with Phase 72 (HS-72-03 renames `/api/companion/*`; HS-72-08 moves the socket) | Both branches stack on `phase-72-one-spine`; the desk subscribes to `hs-*` DOM events (stable across 72-08); rebase is a one-line path fix | A desk story blocked >1 day on a Phase-72 merge |
| Scope magnetism toward a browser-mic recorder | The orb drives the hub recorder (`/live` pattern); browser capture is named Out with the reason (new plumbing + new egress surface) | Any `getUserMedia` call in the diff |

## Decisions made

- **The web Record orb drives the hub's recorder** (`POST /api/meeting/start`,
  exactly like `/live`), not a browser microphone. Same trust posture, zero
  new egress, zero new plumbing.
- **The desk rail is personas only.** `agent` (persona) ≠ `coder` (live
  session) per the Primitive Framework; coder presence stays on the board
  Phase 72 renames.
- **Phase 72's `desk.astro` decomposition watch item is absorbed here** —
  HS-73-01 rebuilds the page as partials; by closeout the 1,732-line
  monolith is gone as a side effect.
- **The `?raw` + `new Function` Alpine loading pattern stays** for this
  surface (the Astro attribute-dropping constraint is real); modularization
  happens inside the factory via composed `scripts/desk/` modules.

## Decisions deferred

- Whether `/companion` (the coder board) eventually merges into the desk as
  a lane — a product call for the owner once the rail exists; flagged in
  HS-73-07, not built.
- A list/table view of primitives on the desk (an in-world toggle) — only if
  the HS-73-04 inventory finds verbs that genuinely want a dense view;
  default is no.
- Sprite icon picker parity (`DioIconPicker`) — nice-to-have; not required
  for inhabitation; backlog candidate if the owner asks.
