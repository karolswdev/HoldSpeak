# Evidence — HS-70-01: The IA spine — nav reframe to the two modes + Studio

**Date:** 2026-06-30
**Verdict:** done. The flat 14-door nav (Live / Review / Configure groups) is
replaced by the four-destination model that states the product's own story in
the chrome: **Home · Dictation · Meetings · Studio ▾ · Settings.** The mental
model is now legible before a click.

## What shipped

- **`web/src/components/TopNav.astro`** — rewritten. The three inline groups
  became three primary links (`Home` → `/`, `Dictation` → `/dictation`,
  `Meetings` → `/history`) plus a **`Studio` disclosure** built on native
  `<details>`/`<summary>` (zero JS, keyboard-native). Studio holds the seven
  browsable advanced surfaces (Workbench, Desk, Agent Desk, Activity, Cadence,
  Commands, Profiles) behind an "ADVANCED" eyebrow, in a floating elevated panel
  (`--elev-2`) on desktop and inline (static) on mobile. It **auto-opens** when
  the active route lives inside it (`studioActive`), and the summary carries a
  subtle "you are here" tint (`.has-active`, no page underbar). The active route
  stays dual-encoded (accent tint + weight + underbar + `aria-current`).
- **`web/src/layouts/AppLayout.astro`** — the `Route` union updated in lockstep
  (`runtime`→`home`, `history`→`meetings`, `+cadence`).
- **Page `current=` slugs updated:** `index.astro` (`home`), `history.astro`
  (`meetings`), `design/check.astro` (`home`), `cadence.astro` (`+current=
  "cadence"`, previously unset so its nav item never lit).

## Decisions recorded (transitional, for later stories)

- **Activity** is parked in Studio here; **HS-70-04** folds it into the Dictation
  surface and drops it from this tier (it is a dictation-support feature, not a
  power tool).
- **Presence** is intentionally **not** a Studio nav item: `/presence` is a
  nav-less HUD overlay (a link there is a dead-end with no way back). It stays
  reached from Settings; the **HS-70-06** Studio *index* may still card it.
- **No routes moved or added** in this story (the spine only). `/history` stays
  the Meetings route until **HS-70-05** decides `/history`↔`/meetings`.

## Proof

- **`screenshots/nav-01-collapsed.png`** — wide, Studio collapsed: `HoldSpeak
  Home · Dictation · Meetings · Studio ▾` with the accent underbar on the active
  Dictation; the TrustChip + ⚙ tail unchanged.
- **`screenshots/nav-02-studio-open.png`** — wide, Studio expanded: the caret
  flips and the ADVANCED panel shows all seven tools in an elevated floating card.
- **`screenshots/nav-03-workbench-active.png`** — on `/workbench`: the Studio
  summary shows the "you are here" tint, the panel auto-opened, and **Workbench**
  is highlighted as the current item (no primary link lit).
- **`screenshots/nav-04-mobile-menu.png`** — narrow (720px), menu open: the
  column nav with Studio expanding **inline** (ADVANCED + the seven tools
  indented), the panel static (not floating).
- **Tests:** `cd web && npm run build` green (17 pages); the route pre-flight
  (`tests/e2e/test_route_preflight.py`) **2 passed** — every route still served,
  listed, and swept for zero page errors under the new nav. Full suite:
  **3045 passed, 37 skipped** (`uv run pytest -q --ignore=tests/e2e/test_metal.py`,
  identical to the Phase-69 baseline). No test asserted the old nav labels/slugs,
  so the rename needed no test edits.
