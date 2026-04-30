# Phase 12 - Workbench Voice

**Last updated:** 2026-04-30 (HS-12-02 + HS-12-03 done; HS-12-04 next).

## Goal

Phase 10 built a working design system but landed on generic
"modern dark workbench" — the project is named for **Amiga
Workbench**, and the visual voice should evoke it. Phase 12 is a
voice pass over the existing design system: same components,
same tokens layer, different *values* and a pixel-rendered UI font.

The aim is to **evoke Workbench 1.3, not emulate it pixel-for-
pixel**. We want:

- The iconic four-color palette (Workbench blue canvas, white
  surfaces, black 1 px hairlines, orange accent).
- Radius-0 across the system (no rounded corners).
- A pixel-rendered UI font for chrome (Topaz-style or VT323),
  with body/code staying mono and legible.
- Hard 1 px borders, no elevation shadows.

We want to **skip** the parts of Workbench that fight dense data:

- The diagonal-stripe title bar pattern on every panel — too
  visually noisy on `/activity` and `/history` lists.
- The full inset/outset gadget bevel grammar on every button — same
  reason. Buttons stay flat-with-hard-border.
- Pixel arrow cursor, clamped 4-color rendering, etc — the *voice*,
  not a museum reproduction.

## Scope

- **In:**
  - Token replatform: palette, radius (all 0), motion review.
  - Self-hosted pixel UI font; body/code stay JetBrains Mono.
  - Component voice pass — Button, Pill, Panel, Toolbar, ListRow,
    EmptyState, InlineMessage, CommandPreview, ConfirmDialog,
    TopNav.
  - Per-route audit + dashboard fixes (oversized hero wordmark,
    over-saturated accent, duplicate toasts, idle-state copy
    redundancy).
  - Refreshed `designer-handoff/` package against the new voice.
- **Out:**
  - New product features or new routes.
  - Pixel-perfect Workbench 1.3 emulation (stripe title bars,
    full gadget bevels, pixel cursor).
  - Light theme tokens (still deferred from phase 10).
  - Backend changes; this is presentation-layer only.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-12-01 | Workbench token map + pixel UI font | done | [story-01-workbench-tokens.md](./story-01-workbench-tokens.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-12-02 | Component voice pass | done | [story-02-component-voice.md](./story-02-component-voice.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-12-03 | Per-route audit + dashboard fixes | done | [story-03-route-audit.md](./story-03-route-audit.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-12-04 | Designer handoff refresh + phase exit | backlog | [story-04-handoff-dod.md](./story-04-handoff-dod.md) | pending |

## Where We Are

Phase 12 is **active**. Phase 11 (Local Connector Ecosystem)
paused with HS-11-01 done; resumes after phase 12 closes.

HS-12-01 ships the values layer: `tokens.css` is replatformed on
the canonical four-colour Workbench palette (blue / white /
black / orange) exposed both as semantic tokens (`--canvas`,
`--text`, `--accent`, status ramps) and as a `--wb-*` reference
set. Every radius collapses to 0, every elevation token is now
`none`, and `--font-ui` resolves to a self-hosted VT323. The
body itself is the blue desktop layer, so anything on the
desktop reads white-on-blue; white-surface components keep their
phase-10 scoped CSS unchanged. The component gallery h1, lead
copy, primary/secondary/danger buttons, and the runtime
dashboard hero all read unmistakably Workbench in the
post-replatform screenshots.

HS-12-02 closed across six review-driven slices. The user
called direction shifts ("font is too greedy", "4 colors is
regarded", "gray-on-gray is illegible") and each became the
next slice's brief — the result is a meaningfully better
design system than the slice before it.

HS-12-03 closed alongside: the dashboard hero now hides the
"HoldSpeak" wordmark fallback at idle (TopNav already shows
it), the toast layer dedupes identical messages, hero copy
trimmed of the redundant "...locally on this machine"
sentence, and the "No tags yet" placeholder removed. Idle
state shows one affordance.

Up next: HS-12-04 (designer handoff refresh + phase exit).

## Source Design

- `designer-handoff/style-handoff.md` — phase-10 baseline (will
  be rewritten by HS-12-04).
- `web/src/styles/tokens.css` — token layer phase 12 replatforms.
- Phase 10 phase status doc — for the "what shipped" context.

## Notes

- The user is the primary audience for the visual voice
  decision: HoldSpeak is named for and inspired by Amiga
  Workbench, and the workbench feel is part of the product's
  identity. "Evoke" not "emulate" means the dashboard should
  look like *something a Workbench fan made for themselves in
  2026*, not a fan-art pixel reproduction.
- The dashboard fixes folded into HS-12-03 are real polish
  items that surfaced during phase-10 review:
  - Oversized hero wordmark duplicates the TopNav brand.
  - Cyan accent is over-saturated for "calm and precise".
  - Duplicate "Failed to load deferred plugin jobs" toasts.
  - Idle-state copy says "press start" three different ways.
