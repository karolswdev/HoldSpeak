# Phase 98 — Native Surfaces

**Status:** SCAFFOLDED (0/9, 2026-07-18) from the owner's standing
verdict ("none of the Desk OS feels like an OS — windows feel like
glued-in HTML panes, zero consistent look and feel") and the 2026-07-18
remediation audit. Phase 97 shipped the window grammar (placement,
depth, motion, one shelf); this phase re-crafts what lives INSIDE the
windows.

**Last updated:** 2026-07-18 (scaffolded).

## Why this phase exists

The audit named the seam mechanically, and it is still fully present:

- **Two visual products on one screen.** Every demoted core is a
  Signal-era web page hosted in a desk window: `page-grid` /
  `span-8` / `span-4` layouts that reflow on **viewport** media
  queries (`react-app.css:1195`) — resize a window narrow on a wide
  screen and its twelve-column grid never notices. A real OS window's
  content answers to the window, not the browser.
- **Double chrome.** Cores wrap their content in Signal `Panel` cards
  — their own fill, border, radius, title, and mono eyebrow — inside a
  window frame that already provides all of that. A card in a window
  reads as a webpage widget, never as an application surface.
- **Raw admin dumps.** `data-list` / `data-row` render whatever keys
  the API returned ("confidence 0", "id unknown", ISO timestamps,
  snake_case values). Article VI says honest; Article VII says quiet —
  a dump is neither.
- **Eyebrows restate titles** inside content ("ATTENTION AND RECEIPTS
  Desk memory") after Phase 97 demoted them from the window head.
- **Button walls.** Row verbs render as permanent `button-row` strips
  under every list item instead of quiet, revealed row actions.

This phase executes Constitution Articles VII (the interface serves —
one quiet grammar) and VIII (native-grade craft) on the window
interiors: one surface idiom, built from the Phase 96 tokens, applied
to all fourteen cores, with the Signal page grammar retired from the
desk. Article IX governs proof: production bundle, real hub, real
viewports, screenshots looked at.

## The surface idiom (the target, named)

1. **One material, no double chrome.** The window frame is the only
   chrome. Content sits directly on `--desk-window-fill`; groups are
   separated by hairline rules and quiet section labels, not nested
   cards.
2. **The window is the viewport.** The surface body is a size
   container; every core layout responds to `@container` width —
   master–detail wide, single column narrow. Viewport-driven grids are
   forbidden in cores.
3. **A denser scale.** OS panels are denser than web pages: surface
   density tokens (row height, padding, body size) in the component
   layer, used by every core.
4. **Rows say what they mean.** Every row is a title plus a meaningful
   detail; timestamps humanized; unknown values omitted, never printed
   as "unknown"/"0".
5. **Verbs have homes.** Primary verbs ride one sticky verb bar at the
   surface top; row verbs reveal on hover/focus; no permanent button
   walls.
6. **One state grammar.** Loading, empty, and error render one shared
   quiet treatment — glyph plus short label, no prose.

## Scope

### In

- a desk-native surface kit (`web/src/desk/surface/`) + `surface.css`
  on component tokens, with the idiom specced in DESIGN_SYSTEM.md
  BEFORE the first core converts;
- a mechanical seam guard: Signal page classes (`page-grid`, `span-*`,
  `data-list`, `data-row`, `signal-eyebrow`, `Panel`, …) forbidden in
  `pages/cores/`, with a per-file allowlist that only shrinks and is
  EMPTY at phase close;
- all fourteen cores re-crafted in the idiom (Dictation, History,
  Live, Activity, Settings, Setup, Workbench, Studio, Components,
  Cadence, Commands, Profiles, Companion, RuntimeDocs);
- dead Signal page CSS pruned once no core uses it;
- docs as floors; the closeout walk extended with a surfaces leg,
  shots at 1440 and 393 looked at.

### Out

- world/object art, grounding, object-to-window morph (The Living
  World, next);
- iPad/Diorama parity (HSM One Grammar on Glass consumes this idiom);
- new surfaces, routes, capabilities, or API changes (re-craft, not
  re-plumb; the wire contracts stay byte-identical);
- the non-desk shells that legitimately remain pages (welcome,
  presence) — they keep the page grammar.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-98-01 | The surface idiom | backlog | [story-01-surface-idiom](./story-01-surface-idiom.md) | — |
| HS-98-02 | Dictation, native | backlog | [story-02-dictation-native](./story-02-dictation-native.md) | — |
| HS-98-03 | Meetings, native | backlog | [story-03-meetings-native](./story-03-meetings-native.md) | — |
| HS-98-04 | The live pair | backlog | [story-04-live-pair](./story-04-live-pair.md) | — |
| HS-98-05 | The config pair | backlog | [story-05-config-pair](./story-05-config-pair.md) | — |
| HS-98-06 | The builder set | backlog | [story-06-builder-set](./story-06-builder-set.md) | — |
| HS-98-07 | The long tail, seam retired | backlog | [story-07-long-tail](./story-07-long-tail.md) | — |
| HS-98-08 | The surface floors, written | backlog | [story-08-docs](./story-08-docs.md) | — |
| HS-98-09 | Closeout: the native walk | backlog | [story-09-closeout](./story-09-closeout.md) | — |

## Where we are

Scaffolded 2026-07-18. Next: HS-98-01 — spec the idiom, build the kit,
arm the seam guard.
