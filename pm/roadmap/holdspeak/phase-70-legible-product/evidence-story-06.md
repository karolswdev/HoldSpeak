# Evidence — HS-70-06: The Studio tier — power features framed and contained

**Date:** 2026-06-30
**Verdict:** done. The six power tools now have one coherent, clearly-secondary
**Studio index** at `/studio`: each framed with a one-line purpose (and state
where relevant), reached from the collapsed nav group. A first-run user is never
dumped into Workbench or Cadence and left asking "what is this".

## What shipped

- **`web/src/pages/studio.astro`** — the Studio index. An "Advanced" eyebrow +
  "Studio" + a one-line lede ("Power tools for when you want them. Optional; the
  two modes need none of this."), then a grid of six `.signal-card` tool cards:
  - **Workbench** — "Wire primitives into a runnable workflow on a node canvas."
  - **Desk** — "Author meetings, notes, agents and more on a spatial desk."
  - **Agent Desk** — "Your coding agents, and the ones waiting on you."
  - **Cadence** — "A background chief-of-staff that pushes with receipts." +
    an honest **"Off by default"** state chip.
  - **Commands** — "Map a spoken keyword to an action."
  - **Profiles** — "Runtime and model profiles, assignable per agent."
  Each card is a link to the tool; the tools keep their own routes and
  behaviour (Decision B: framed, not re-implemented).
- **`holdspeak/web/routes/pages.py`** — a `/studio` route + `PAGE_ROUTES` entry.
- **`web/src/components/TopNav.astro`** — the dropdown's "ADVANCED" eyebrow
  became a **link to `/studio`** ("ADVANCED →"); `studioActive` now also lights
  the summary when you are on `/studio`; the `studio` slug added to the `Route`
  union (TopNav + AppLayout).

## Framing (the point)

The index reads as advanced and optional, visually distinct from the two-mode
front door; a tool that is off says so (Cadence's "Off by default" chip). The
first-run path never lands here (HS-70-03: first-run users go to `/welcome` →
Home, and Home's quiet Studio link is a dashed, secondary affordance).

## Proof

- **`screenshots/studio-index.png`** — `/studio`: the six framed cards (glyphs +
  one-line purposes + "Open →"), Cadence tagged "Off by default", with the nav's
  Studio summary active and its dropdown showing the "ADVANCED →" index link.
- **`screenshots/studio-dropdown.png`** — the dropdown with the "ADVANCED →"
  link above the six tools.
- **Tests:** route pre-flight **2 passed** (`/studio` served + swept, zero page
  errors); full suite **3045 passed, 37 skipped**; build green (18 pages).
