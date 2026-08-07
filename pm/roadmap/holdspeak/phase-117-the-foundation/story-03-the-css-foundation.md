# HS-117-03 — The CSS foundation

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** —
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

`desk.css` is 6,072 lines in a single file. Every component's styles
live together under `.desk-next`, organized by story-era comments
(HS-73 through HS-116). Adding a workbench card rule means scrolling
past the dictation deck (1,155 lines), mission control (614 lines),
and delivery surfaces (394 lines). Two components have already
escaped to co-located CSS (`RepoWindow.css`, `RoadmapWindow.css`);
the other ~30 have not.

When this story ships, `desk.css` is replaced by co-located CSS
modules imported by the components that own them. A single
`desk-tokens.css` re-exports the design-system custom properties
each module needs. The desk looks pixel-identical; the CSS is
navigable.

**Articles served:** VIII (native-grade craft — co-located styles are
a speed multiplier), VI (honest construction — each component owns
its appearance).

## Deliverables

### 1. Create `desk-tokens.css`

Create `web/src/desk/desk-tokens.css` that re-exports the subset of
`styles/tokens.css` custom properties consumed by desk modules:
`--bg`, `--border`, `--surface-2`, `--text`, `--text-faint`,
`--text-muted`, `--font-mono`, `--accent-tint`, `--border-subtle`,
`--duration-short`, `--ease-standard`, `--wash-2`, `--danger-fill`,
and the desk-specific geometry tokens (`--desk-z-stage`,
`--desk-window-bevel`, `--desk-window-etch`, `--desk-window-pad-x`,
`--desk-surface-*`). This file is import-only — it declares no rules.

Do NOT duplicate token values. Use `@import` from `styles/tokens.css`
or re-reference via `var()`. The file is a convenience index, not a
second source of truth.

### 2. Extract the seven largest sections into co-located modules

Split by section boundaries (the `/* ── ... ── */` comments already
mark clean cuts):

| Module file | Source lines | Class prefix | Co-locate next to |
|---|---|---|---|
| `workbench-config.css` | 47-632 (~585 lines) | `.wb-config`, `.wb-card` | `WorkbenchWindow.tsx` |
| `speak.css` | 4797-5952 (~1,155 lines) | `.desk-speak-*`, `.desk-dictation-*` | `DictationCore.tsx` or `desk/speak/` |
| `mission-control.css` | 2240-2853 (~614 lines) | `.desk-mc-*` | `MissionControl.tsx` |
| `delivery.css` | 3667-4060 (~394 lines) | `.desk-dlv-*`, `.desk-pr-*` | delivery components |
| `window-chrome.css` | 1559-1809 + 4122-4384 (~510 lines) | `.desk-window-*` | `DeskWindow.tsx` |
| `pullout.css` | 1400-1559 + 1810-1949 (~300 lines) | `.desk-pullout-*` | `Pullout.tsx` |
| `dock.css` | 4122-4384 dock subset (~130 lines) | `.desk-dock-*` | `Dock` (inside DeskWindow.tsx today) |

Each module file imports `desk-tokens.css`. Each consuming component
adds `import "./workbench-config.css"` (Vite CSS module import).

### 3. Extract the remaining mid-size sections

| Module file | Source lines | Class prefix |
|---|---|---|
| `chrome-menus.css` | 686-1223 (~540 lines) | `.desk-menu-*`, `.desk-chip-*`, `.desk-deck-*` |
| `attention.css` | 3235-3513 (~280 lines) | `.desk-attention-*` |
| `session-pullout.css` | 2942-3053 (~110 lines) | `.desk-session-*` |
| `record-orb.css` | 1950-2013 (~65 lines) | `.desk-orb-*` |
| `agent-rail.css` | 2014-2109 (~95 lines) | `.desk-rail-*` |
| `speak-to-fill.css` | 2110-2207 (~100 lines) | `.desk-stf-*` |
| `list-view.css` | 3514-3666 (~150 lines) | `.desk-list-*` |
| `inline-editor.css` | 1224-1399 (~175 lines) | `.desk-inline-*` |

### 4. Leave a thin `desk.css` remainder

After extraction, `desk.css` retains only:

- The `.desk-next` root scope reset (lines 6-46, ~40 lines).
- The GL world base (lines 633-685, ~50 lines).
- The `@import` list pulling in every extracted module.

Target: `desk.css` drops from 6,072 to under 150 lines.

### 5. Verify no duplicate selectors or broken specificity

After the split, run a CSS audit:
- `grep -r` for duplicate class definitions across modules.
- Confirm no module relies on selector ordering from the monolith
  (each module must be order-independent within `.desk-next`).

## What NOT to do

- Do NOT rename any CSS class. The split is mechanical — every
  selector string stays identical.
- Do NOT adopt CSS Modules (`:local()` / `*.module.css`). The desk
  uses global class names scoped by `.desk-next`; that contract stays.
- Do NOT refactor the token system. `styles/tokens.css` and
  `tokens.gen.ts` are owned by the design-system layer.
- Do NOT change the visual output. This is a zero-delta refactor.
- Do NOT create per-component `*.module.css` files that hash class
  names. The GL scene model reads class names by string.

## Test plan

1. `npx tsc --noEmit` — zero type errors (CSS imports are untyped).
2. `npx vitest run` — all existing web tests pass.
3. Playwright screenshot walk at 1440px and 393px — every desk
   surface renders pixel-identically to the pre-split baseline.
4. `grep -r "desk-next" web/src/desk/*.css` — confirms no duplicate
   selectors across module boundaries.
5. Dev server hot-reload — each module change triggers only its
   own component's style update.

## Estimated scope

~0 net lines changed (pure split). 15 new CSS module files created.
`desk.css` drops from 6,072 to ~120 lines of imports + root scope.
Each component gains one `import` line.
