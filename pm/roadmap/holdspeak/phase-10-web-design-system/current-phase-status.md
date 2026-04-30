# Phase 10 - Web Design System & Character Pass

**Last updated:** 2026-04-29 (HS-10-12 / motion + a11y pass).

## Goal

Take the HoldSpeak web runtime from a sterile, inconsistent set of
hand-rolled HTML pages to a coherent, modern, character-bearing local
workbench. Establish a real design system (tokens + components +
identity) on a static-first framework, then rebuild every route on top
of it. The exit artifact is a refreshed `designer-handoff/` package and
a frontend whose look and feel match the product's intent: quiet,
dense, trustworthy, local.

The starting point is documented in `designer-handoff/style-handoff.md`,
`designer-handoff/ux-inventory.md`, and `designer-handoff/screenshots/`.
Each of the five page templates currently carries its own inline
`<style>` block; navigation, empty states, command previews,
confirmations, and status pills are reinvented per page; and there is
no identity layer that says "this is HoldSpeak."

## Scope

- **In:**
  - Astro + Open Props bootstrap, building into `holdspeak/static/`.
  - Design token layer (color, typography, spacing, radius, motion),
    dark theme v1, `prefers-reduced-motion` support.
  - Core component library (Button, Pill, Panel, Toolbar, ListRow,
    EmptyState, InlineMessage).
  - Unified TopNav and route identity component.
  - HoldSpeak identity layer (app mark, hold-to-talk motif, local-only
    privacy pill, focus-ring grammar).
  - Per-route rebuilds on the new system: `/`, `/activity`, `/history`,
    `/dictation`.
  - Standardized `CommandPreview` component (gh, jira, dry-run).
  - Standardized destructive-action confirmation pattern.
  - Motion + accessibility pass.
  - Refreshed `designer-handoff/` screenshots and resolved style
    questions.
- **Out:**
  - Light theme tokens (deferred; tracked as an open style question).
  - New product features or new routes.
  - Marketing/landing surface.
  - Cloud-served assets or remote fonts (everything stays local).
  - Backend API changes; this phase is presentation-layer only.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-10-01 | Astro + Open Props bootstrap | done | [story-01-astro-bootstrap.md](./story-01-astro-bootstrap.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-10-02 | Design token layer | done | [story-02-design-tokens.md](./story-02-design-tokens.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-10-03 | Core component library | done | [story-03-core-components.md](./story-03-core-components.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-10-04 | Unified TopNav and route identity | done | [story-04-top-nav.md](./story-04-top-nav.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-10-05 | HoldSpeak identity layer | done | [story-05-identity-layer.md](./story-05-identity-layer.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-10-06 | `/` runtime dashboard rebuild | done | [story-06-dashboard-rebuild.md](./story-06-dashboard-rebuild.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-10-07 | `/activity` rebuild | done | [story-07-activity-rebuild.md](./story-07-activity-rebuild.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-10-08 | `/history` rebuild | done | [story-08-history-rebuild.md](./story-08-history-rebuild.md) | [evidence-story-08.md](./evidence-story-08.md) |
| HS-10-09 | `/dictation` rebuild | done | [story-09-dictation-rebuild.md](./story-09-dictation-rebuild.md) | [evidence-story-09.md](./evidence-story-09.md) |
| HS-10-10 | `CommandPreview` component | done | [story-10-command-preview.md](./story-10-command-preview.md) | [evidence-story-10.md](./evidence-story-10.md) |
| HS-10-11 | Destructive-action confirmation pattern | done | [story-11-destructive-confirmation.md](./story-11-destructive-confirmation.md) | [evidence-story-11.md](./evidence-story-11.md) |
| HS-10-12 | Motion + accessibility pass | done | [story-12-motion-a11y.md](./story-12-motion-a11y.md) | [evidence-story-12.md](./evidence-story-12.md) |
| HS-10-13 | Designer handoff refresh + phase exit | backlog | [story-13-handoff-refresh-dod.md](./story-13-handoff-refresh-dod.md) | pending |

## Where We Are

Through HS-10-08, four of the five route rebuilds are complete:
`/` (HS-10-06), `/activity` (HS-10-07), and `/history` + `/settings`
(HS-10-08). All run through `AppLayout` with token-driven scoped CSS,
self-hosted Alpine, and verbatim-ported factories
(`dashboard-app.js`, `activity-app.js`, `history-app.js`). Combined,
the legacy `dashboard.html` (2,819) + `activity.html` (940) +
`history.html` (2,508) — 6,267 lines of hand-written HTML/CSS/JS —
have been replaced by Astro pages that pull every visual value from
`tokens.css`.

All five route surfaces (`/`, `/activity`, `/history` + `/settings`,
`/dictation`, `/docs/dictation-runtime`) now serve from the Astro
build under `AppLayout`. The legacy `holdspeak/static/*.html` files
that previously hand-rolled topbars / styles / inline scripts are
gone — combined removal of `dashboard.html` (2,819) +
`activity.html` (940) + `history.html` (2,508) + `dictation.html`
(1,381) + `dictation-runtime-setup.html` (95) = **7,743 lines** of
ad-hoc presentation code displaced by token-driven Astro pages.

The dry-run trace on `/dictation` is the first production consumer
of `CommandPreview` (HS-10-10): final text + each stage render
through `<figure class="cmd cmd--{tone}">` markup, and stages with
warnings flag in `cmd--danger`.

HS-10-11 lands the destructive-action confirmation pattern: a single
native `<dialog>` mounted by `AppLayout` plus a
`window.holdspeakConfirm({...}) → Promise<boolean>` dispatcher. Every
destructive call site across `/`, `/activity`, `/history`, and
`/dictation` now routes through it — the eight sites listed in the
HS-10-11 evidence file. `grep -rn 'confirm(' web/src/` returns no
matches; the only `window.confirm` call left in the legacy
`dashboard-app.js` is gone.

HS-10-12 closes the polish gap: a global `hs-pulse` keyframe + an
`.is-live` modifier animate the *dot* on recording / stopping /
analyzing / connecting pills, the hero state-change eases via
motion tokens, the ConfirmDialog gains a 120 ms close animation
that matches its open animation, and every decorative inline SVG
in `web/src/` carries `aria-hidden="true"`. Reduced-motion users
collapse all of it via the existing `tokens.css:144` global rule.
A keyboard-only walkthrough of the four canonical workflows
completes without dead-ends.

Up next: HS-10-13 (designer handoff refresh + phase exit).

## Source Design

- `designer-handoff/style-handoff.md` — current visual language,
  desired direction, component families to formalize, open style
  questions.
- `designer-handoff/ux-inventory.md` — routes, surfaces, gaps, design
  deliverables.
- `designer-handoff/functional-handoff.md` — workflows and critical
  states each route must support.
- `designer-handoff/screenshots/` — current implementation, captured
  via `capture-screenshots.py`.
- `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — the web-first runtime
  contract this phase rebuilds against.
