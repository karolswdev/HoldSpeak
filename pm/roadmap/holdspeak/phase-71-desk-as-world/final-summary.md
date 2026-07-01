# Phase 71 — The Desk, as a World (the web diorama): final summary

**Status:** CLOSED (8/8) — 2026-07-01. Branch `phase-71-desk-as-world`.

## Why this phase existed

After Phase 70 made the web legible (four doors, one arrival), the owner said
the web still felt "nowhere near the look and feel of the iOS app". Shown the two
"Desks" side by side — the iPad's 2.5D spatial diorama vs. the web's flat
card-list — the diagnosis was clear: the gap was **paradigm, not polish**. Phase
69 matched tokens, Phase 70 fixed the IA, but the web still *read as a document*
while the iPad *read as a world*. The owner chose the full fix: **port the
diorama to the web `/desk`.**

The scaffold's technical map found the good news: the web `/desk` already loads
every primitive live from the same `/api/*` endpoints the iPad uses. So this was
**a rendering change plus one sprite-asset copy**, not new plumbing. No backend
was touched; the suite held at **3045 passed** across all eight stories.

## What shipped (the eight stories)

1. **The room** — a fixed `.desk-stage`: the DioPal gradient + an animated warm
   radial spotlight + a canvas of rising dust motes. `/desk` stopped being flat
   black.
2. **The sprite pipeline** — 67 pixel-art PNGs copied verbatim from `apple/App/`
   into `web/public/desk/sprites/`, + a picker (`sprites.js`) that matches
   `SpriteStore.swift`'s djb2 stable hash exactly (64-bit BigInt), so an id picks
   the same variant the iPad would.
3. **Objects that float** — every primitive renders as a floating sprite with a
   detached ground shadow + a per-kind glow, via pure CSS keyframes (no rAF).
   The card-list moved under a collapsed "Browse as a list". **The world moment.**
4. **Free placement** — drag to arrange, persisted per-device to
   `localStorage["hs.diorama.pos"]` (local-only, matching the iPad contract);
   density-aware `looseHome` for untouched objects; a "Tidy" reset.
5. **Zones + dive** — directories become painted shelf-zones; drag an object onto
   one to **file** it (real `PUT /api/directories/{id}/members/{pid}`); click to
   **dive** in (filter to members) with a back control.
6. **Life + open** — Qlippy lives in the corner (gated on `presence.mascot`, off
   by default); freshly-created objects get a NEW flourish; tap opens an object
   (meeting → `/history`, others reveal the card).
7. **Docs + the nav decision** — owner chose **celebrate on Home + keep in
   Studio**: Home gains a "The Desk →" entry, the four-door nav stays intact.
   `docs/WEB_DESK.md` + a POSITIONING Desk paragraph.
8. **Closeout** — the side-by-side vibe test + the full walk, proven; this.

## The result

`/desk` is a warm, lit, spatial world: hand-drawn objects float with depth, you
arrange them by hand, file them into shelves and dive through, with Qlippy in the
corner — the same felt world as the iPad, from the same live data. The two-mode
cockpits stay clean, fast dashboards (owner call); only `/desk` became the world,
celebrated with an entry on Home.

## Proof

- The side-by-side: `screenshots/08-web-desk-hero.png` vs. the iPad
  `2001-ipad-wide.png` — one world.
- Per-story screenshots + Playwright proofs (drag persists; file fires the real
  `PUT`; dive; Qlippy; tap-to-open → `/history`).
- Route pre-flight green (zero page errors on `/desk`); full suite **3045
  passed, 37 skipped** (constant across the phase); `web/public/desk/sprites`
  committed; `_built` never committed.

## Honest follow-ups (not blockers)

- **Zones don't drag yet** — they auto-lay across the top (their geometry store
  is stubbed in `zoneStyle`); making shelves draggable is a small follow-on.
- **Object variety on web is a subset** — meetings/notes/kbs/agents have full
  pools; chains/workflows/artifacts/directories share a fallback sprite until
  their own art is drawn.
- **The list detail** ("Browse as a list") is still the authoring path for the
  richer create/run forms; a fully in-world create/run flow (the iPad's Record/
  New orbs) is a natural next epic.
- **Nav**: the Desk is celebrated on Home + kept in Studio (owner's call);
  promoting it to a top-level door remains a one-line change if ever wanted.

## For the next agent

The diorama engine is `web/src/pages/desk.astro` (markup + `is:global` CSS) +
`web/src/scripts/desk-app.js` (worldObjects / objStyle / drag / zones / life) +
`web/src/scripts/desk/sprites.js` (the picker) + `web/public/desk/sprites/`. It
is a rendering layer over the untouched `/api/*` data seam. The vibe bar
(AGENT-BRIEF §1) is the standard: it must read as a world.
