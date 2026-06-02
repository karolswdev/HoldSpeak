# HoldSpeak web UX audit (HS-30-01)

**Date:** 2026-06-01. **Captured from:** the built front-end served via
`astro preview` at `http://127.0.0.1:4321/_built/`, screenshotted with puppeteer
at 1440×900 (idle / no-backend state — the chrome, IA, and visual grammar are
what's under audit, not live data). Before screenshots: `evidence/before/before-*.png`.

This audit is grounded in the `ui-ux-pro-max` skill (`ux` + `product` domains —
output captured in `evidence-story-01.md`). It names problems only; the fix is in
`ia-spec.md`.

## Method

- Walked all five routes + the `/design/components` gallery in the running build.
- Extracted each route's structural skeleton from source (regions, tabs, primary
  actions, Alpine factory) — see `evidence-story-01.md` for the per-route outline.
- Cross-checked against `ui-ux-pro-max` `ux` guidelines (heading hierarchy,
  color-only signalling, sticky-nav, modular type scale) and the `product`
  recommendation for this product class.

## Product framing (skill-grounded)

`ui-ux-pro-max` `product` search maps HoldSpeak to two overlapping classes:

- **Developer Tool / IDE** → *Dark Mode (OLED) + Minimalism*; dashboard style
  *Real-Time Monitor + Terminal*; palette *dark theme + focus accent*.
- **Productivity Tool** → *Flat Design + Micro-interactions*; dashboard style
  *Drill-Down Analytics*; *clear hierarchy + functional colours*.

Both point to a **dark, minimal, real-time-monitor** surface with a focused
accent — which is the "Signal" direction. The current Workbench skin is the
opposite of every one of those recommendations.

## Global / shell problems

The whole product inherits `AppLayout.astro` + `TopNav.astro` and the
`tokens.css` Workbench grammar, so these apply on every route:

1. **Saturated-blue full-bleed desktop fights the content.** `--wb-blue #0055AA`
   is the page background; content is white panels floating on it
   (`before-runtime.png`). High chroma over the whole viewport is fatiguing and
   provides *no* figure/ground hierarchy beyond raw black-on-white contrast —
   every panel shouts at the same volume.
2. **Pixel display font (VT323) on every title and nav item** is low-legibility
   and reads as a retro toy, undercutting a "local, private, trustworthy" tool.
   Visible on "Transcript stream", "Intelligence", "Topics", the nav, and every
   panel header. (Skill `ux`: a consistent *modular type scale* aids scanning;
   the pixel face actively hurts it.)
3. **No depth, no radius, hard 1px black hairlines everywhere.** `--radius-* = 0`,
   `--elevation-* = none`. Nothing is grouped or elevated; the eye gets no help
   separating primary content (live transcript) from secondary (the intel rail).
4. **Navigation is a flat, ungrouped 5-link strip** (Runtime · Activity · History
   · Dictation · Companion) with no signal of which is the primary daily surface
   vs configuration vs archive. Active state is a thin underline — partly
   **colour-only** (skill `ux`, *Color Only*, severity High: don't signal by
   colour alone). It wraps on narrow widths with no deliberate responsive
   strategy (no menu/overflow).
5. **Status is fragmented.** The only persistent status is a "local-only" pill;
   connection state is buried in the dashboard's stat grid ("Reconnecting in
   2s…") and surfaced elsewhere as **overlapping error toasts** that collide with
   panel content ("Failed to load deferred plugin jobs", "Connection lost.
   Reconnecting…" sit on top of the Summary/Action-items panels in
   `before-runtime.png`). Error handling is noisy and unplaced.
6. **No global search / command affordance** despite several deep surfaces.

## Information-architecture problems (cross-route)

7. **Global Settings is buried as tab 6 of 6 inside History.** Hotkey, Whisper
   model, theme, devices, cloud-intel config, diarization — all global app
   settings — live under **History → Settings** (`history.astro` lines 632–851).
   Settings is not history; this is the single worst discoverability failure.
8. **History is overloaded** — one 2161-line page with six unrelated tabs
   (Meetings, Action items, Speakers, Projects, Intel queue, Settings) plus a
   meeting-detail modal. It conflates archive browsing, cross-cutting work,
   entity management, ops, and settings into one route.
9. **"My work" (action items) is fragmented across three places** — the dashboard
   rail, History → Action items, and inside each Project detail — with no single
   canonical home, so the user can't answer "what do I owe?" in one look.
10. **Ops surfaces are duplicated.** "Deferred plugin jobs" controls appear on the
    dashboard rail *and* in History → Intel queue, with overlapping filter/retry
    controls — two places to do the same operational task.
11. **Dictation crams 7 tabs** (Readiness, Blocks, Project KB, Project Context,
    Agent Hooks, Runtime, Dry-run) with no progressive disclosure — first-run
    setup, persistent config, and a one-off dry-run tool all at the same level.
12. **Heading hierarchy is inconsistent** across routes (some pages open `h1`,
    others jump straight to panel `h2`/`h3`), which the skill flags (`ux`,
    *Heading Hierarchy*, Medium) for both scanning and screen-reader nav.

## Per-route notes

- **Runtime (`index.astro`)** — the flagship and the densest Workbench markup.
  The live transcript (the point of the page) and the 8-panel intel rail compete
  at equal weight; the rail is a stack of mismatched white boxes. Primary action
  ("Start meeting") is well-placed but the surrounding stat grid and error toasts
  dilute it. *This is the page that most needs hierarchy + depth.*
- **Dictation (`dictation.astro`)** — powerful but heavy; the dry-run pipeline
  trace (its signature feature) is cramped in the hairline grid. Needs
  progressive disclosure and a calmer form treatment.
- **History (`history.astro`)** — see IA problems 7–10. The meeting-detail modal
  and the structured artifact renders are genuinely good content trapped in an
  overloaded shell.
- **Activity (`activity.astro`)** — a reasonable two-column rail/main, but every
  panel is a hard white box; the candidate "preview vs saved" distinction relies
  on a dashed-vs-solid border (subtle, and **colour/линеweight-only**).
- **Companion (`companion.astro`)** — cleanest IA (read-only monitor: summary
  cards → selected target → waiting list → blockers). Mostly needs the new skin,
  not restructuring. A good template for the shared card/status patterns.

## What carries over (keep)

- The **route set itself** is right (5 surfaces map to 5 real jobs).
- **Companion's** information shape is a good model for the shared patterns.
- The **structured artifact renders** in History (mermaid, decisions, ADR, risk
  table, etc.) are valuable — restyle, don't remove.
- **Alpine bindings + API contracts** are sound; this is a presentation problem,
  not a behaviour one.

## Top priorities for the redesign

1. Replace the saturated-blue/white/pixel/hairline grammar with a dark, layered,
   depth-bearing system (Signal) — fixes #1–3, 12.
2. Re-group navigation and **lift Settings out of History** into a global
   destination — fixes #4, 7, 8.
3. Give "my work" / action items a single canonical home and de-duplicate the ops
   surfaces — fixes #9, 10.
4. One consistent page-header + panel + empty/loading/**error** pattern across all
   routes (no overlapping toasts) — fixes #5, 12.
5. Progressive disclosure on Dictation — fixes #11.
