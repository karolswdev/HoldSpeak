# Phase 10 - Web Design System & Character Pass

**Last updated:** 2026-04-28 (HS-10-04 unified TopNav shipped).

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
| HS-10-05 | HoldSpeak identity layer | backlog | [story-05-identity-layer.md](./story-05-identity-layer.md) | pending |
| HS-10-06 | `/` runtime dashboard rebuild | backlog | [story-06-dashboard-rebuild.md](./story-06-dashboard-rebuild.md) | pending |
| HS-10-07 | `/activity` rebuild | backlog | [story-07-activity-rebuild.md](./story-07-activity-rebuild.md) | pending |
| HS-10-08 | `/history` rebuild | backlog | [story-08-history-rebuild.md](./story-08-history-rebuild.md) | pending |
| HS-10-09 | `/dictation` rebuild | backlog | [story-09-dictation-rebuild.md](./story-09-dictation-rebuild.md) | pending |
| HS-10-10 | `CommandPreview` component | backlog | [story-10-command-preview.md](./story-10-command-preview.md) | pending |
| HS-10-11 | Destructive-action confirmation pattern | backlog | [story-11-destructive-confirmation.md](./story-11-destructive-confirmation.md) | pending |
| HS-10-12 | Motion + accessibility pass | backlog | [story-12-motion-a11y.md](./story-12-motion-a11y.md) | pending |
| HS-10-13 | Designer handoff refresh + phase exit | backlog | [story-13-handoff-refresh-dod.md](./story-13-handoff-refresh-dod.md) | pending |

## Where We Are

Phase 10 is scaffolded and ready to begin. Phase 9 (assisted activity
enrichment) is closing out; once HS-9 is `done`, work on HS-10-01 can
start. The design phase is sequenced ahead of the connector ecosystem
(now phase 11) so that any connector packs developed in phase 11 land
on top of the standardized component grammar instead of cementing the
current ad-hoc per-page styles.

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
