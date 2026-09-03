# HoldSpeak Surface Library Atlas

Pixel-perfect recreation reference for plain HTML + inline styles.
Every value resolved to its literal; no var() references remain.

Source barrel: `web/src/desk/surface/index.ts`

---

## 1. GLOBAL TOKENS (resolved values)

### Page / desk background

| Surface       | Value                                                                                         |
|---------------|-----------------------------------------------------------------------------------------------|
| Desk stage    | `background: repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(255,255,255,0.02) 3px, rgba(255,255,255,0.02) 4px), repeating-linear-gradient(-45deg, transparent, transparent 3px, rgba(255,255,255,0.02) 3px, rgba(255,255,255,0.02) 4px), #0e0f13;` |
| --bg          | `#0e0f13`                                                                                     |
| --surface-1   | `#15171d` (window body fill, canvas)                                                          |
| --surface-2   | `#1c1f27` (title bar rest, footer, wells raised fill, gadget fill)                            |
| --surface-3   | `#242833` (title bar front window, gadget hover fill)                                         |
| --desk-window-fill   | `#15171d` (= surface-1)                                                                |
| --desk-window-head-fill | `#1c1f27` (= surface-2)                                                             |
| --desk-window-head-front | `#242833` (= surface-3, front window head)                                          |
| --desk-panel-fill | `#0e0f13` (= bg)                                                                          |
| --desk-window-well | `rgba(0,0,0,0.28)` (sunken well fill)                                                    |
| --desk-terminal-screen | `#0f1115`                                                                              |

### Borders

| Token               | Value                          |
|----------------------|--------------------------------|
| --border             | `#2a2e3e` (solid 1px)          |
| --border-strong      | `#363b50` (front/focused)      |
| --border-subtle      | `rgba(255,255,255,0.06)`       |
| --desk-window-keyline| `#363b50` (= border-strong)    |

### Radii

ALL radii are `2px`. Every component uses `border-radius: 0` or `2px`.
`--radius-xs` through `--radius-pill` all resolve to `2px`.
`--desk-window-radius: 2px`. No rounded corners anywhere in Signal Workbench.

### Bevels and etches (the depth grammar)

| Token                  | Value                                                                                 |
|------------------------|---------------------------------------------------------------------------------------|
| --bevel-light          | `rgba(255,255,255,0.14)` (top-left highlight on raised surfaces)                      |
| --bevel-dark           | `rgba(0,0,0,0.40)` (bottom-right shadow on raised surfaces)                          |
| --etch-light           | `rgba(255,255,255,0.07)` (bottom-right highlight on sunken surfaces)                  |
| --etch-dark            | `rgba(0,0,0,0.30)` (top-left shadow on sunken surfaces)                              |
| --desk-window-bevel    | `inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40)`         |
| --desk-window-etch     | `inset 1px 1px 0 rgba(0,0,0,0.30), inset -1px -1px 0 rgba(255,255,255,0.07)`         |

### Shadows and washes

| Token           | Value                          |
|-----------------|--------------------------------|
| --elev-0        | `none`                         |
| --elev-1        | `0 1px 2px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)` |
| --desk-window-shadow | `none`                    |
| --wash-1        | `rgba(255,255,255,0.035)`      |
| --wash-2        | `rgba(255,255,255,0.05)`       |
| --surface-hover | `rgba(255,255,255,0.04)`       |
| --surface-active| `rgba(255,255,255,0.07)`       |
| --shade-1       | `rgba(0,0,0,0.3)`             |
| --shade-2       | `rgba(0,0,0,0.62)`            |
| --gleam-1       | `rgba(255,255,255,0.07)`       |
| --gleam-2       | `rgba(255,255,255,0.09)`       |
| --gleam-3       | `rgba(255,255,255,0.22)`       |

### Font stacks

| Token          | Value                                                                                  |
|----------------|----------------------------------------------------------------------------------------|
| --font-display | `"Space Grotesk", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` |
| --font-ui      | `"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`        |
| --font-mono    | `"JetBrains Mono", "SFMono-Regular", "SF Mono", Consolas, "Liberation Mono", monospace` |

The MONO face is used for: all section labels, all gadget labels, all tokens, all chips, all footer text, all ledger content, all state chips, all surface-detail text. The UI face (`--font-ui` / `--font-display`) is used only for display-size headings and the window title, and the body-sized primary text in the material renderer.

### Type ramp (every step with its use)

| Role              | font-size     | px  | weight | line-height | letter-spacing | transform | font-family   |
|-------------------|---------------|-----|--------|-------------|----------------|-----------|---------------|
| Display           | 1.625rem      | 26  | 650    | 1.15        | -0.01em        | none      | font-display  |
| Primary           | 0.9375rem     | 15  | 600    | 1.4         | (inherit)      | none      | (inherit)     |
| Body (surface)    | 0.8125rem     | 13  | (inherit) | (inherit)| (inherit)      | none      | (inherit)     |
| Detail            | 0.75rem       | 12  | (inherit) | (inherit)| (inherit)      | none      | (inherit)     |
| Section label     | 10px          | 10  | 600    | 1           | 0.06em         | uppercase | font-mono     |
| Label compact     | 10px          | 10  | 600    | 1           | 0.04em         | uppercase | font-mono     |
| Label wide        | 10px          | 10  | 600    | 1           | 0.08em         | uppercase | font-mono     |
| Eyebrow           | 10px          | 10  | 700    | (inherit)   | 0.06em         | uppercase | font-mono     |
| Gadget group label| 10px          | 10  | 600    | (inherit)   | 0.06em         | uppercase | font-mono     |
| TransportKey word | 9px           | 9   | 650    | 1           | 0.08em         | uppercase | font-mono     |
| LedMeter label    | 9px           | 9   | 600    | 1           | 0.08em         | uppercase | font-mono     |
| Gadget row label  | 12px          | 12  | 500    | (inherit)   | (inherit)      | none      | font-mono     |
| Ledger row        | 12px          | 12  | (inherit) | (inherit)| (inherit)      | none      | font-mono     |
| Button            | 12px          | 12  | 600    | 1           | (inherit)      | none      | font-mono     |
| Button sm (dense) | 11px          | 11  | 600    | 1           | (inherit)      | none      | font-mono     |
| LG (window title) | 1.0625rem     | 17  | 700    | (inherit)   | (inherit)      | none      | font-display  |

### Accent / color system (resolved)

| Token           | Hex / Value               | Use                                              |
|-----------------|---------------------------|--------------------------------------------------|
| --accent        | `#a86e4a`                 | Primary verb fills, selected borders, focus rings |
| --accent-hover  | `#bc8058`                 | Primary verb hover                                |
| --accent-press  | `#936041`                 | Primary verb pressed                              |
| --accent-tint   | `rgba(168,110,74,0.12)`   | Selected row bg, recommended card wash            |
| --accent-glow   | `rgba(168,110,74,0.28)`   | Glow-accent shadow                                |
| --accent-cool   | `#5b8def`                 | Cool blue (tier light, delivery)                  |
| --text          | `#f2f3f5`                 | Primary text                                      |
| --text-muted    | `#9ba2b0`                 | Secondary text, labels                            |
| --text-faint    | `#767e8d`                 | Tertiary text, faint labels                       |
| --text-on-accent| `#f2f3f5`                 | Text on accent fills                              |
| --ok            | `#34d399`                 | Success / active / ACTIVE status / lamp on        |
| --ok-strong     | `#10b981`                 | Success emphasis                                  |
| --ok-soft       | `rgba(52,211,153,0.12)`   | Success notice bg                                 |
| --warn (--warn-signal)| `#fbbf24`           | Warning state                                     |
| --warn-soft     | `rgba(251,191,36,0.12)`   | Warning notice bg                                 |
| --danger (--danger-signal)| `#f87171`       | Failure state, error text                         |
| --danger-fill   | `#dc2626`                 | Danger button fill, close verb hover              |
| --danger-soft   | `rgba(248,113,113,0.12)`  | Danger notice bg                                  |
| --info          | `#56c7f5`                 | Working state, info notice                        |
| --info-soft     | `rgba(86,199,245,0.12)`   | Info notice bg                                    |

### Spacing tokens (resolved)

| Token    | Value     |
|----------|-----------|
| --space-1| 0.25rem (4px)  |
| --space-2| 0.5rem (8px)   |
| --space-3| 0.75rem (12px) |
| --space-4| 1rem (16px)    |
| --space-5| 1.5rem (24px)  |
| --space-6| 2rem (32px)    |

### Sizing tokens

| Token             | Value | Use                                       |
|-------------------|-------|-------------------------------------------|
| --size-touch      | 40px  | Row glyph tile                            |
| --size-key        | 48px  | TransportKey square                       |
| --size-chip       | 27px  | desk-chip height                          |
| --size-btn        | 28px  | Button min-height / compact key height    |
| --size-icon-sm    | 16px  | CheckGadget well, small icons             |
| --size-icon-md    | 20px  | In-well mic, row glyphs                   |
| --size-icon-lg    | 32px  | Large icon                                |

### Surface component tokens

| Token                        | Value        |
|------------------------------|--------------|
| --desk-surface-row-h         | 40px         |
| --desk-surface-row-pad-x     | 10px         |
| --desk-surface-gap           | 2px          |
| --desk-surface-section-gap   | 18px         |
| --desk-surface-label-size    | 0.6875rem (11px) |
| --desk-surface-body-size     | 0.8125rem (13px) |
| --desk-surface-detail-size   | 0.75rem (12px)   |
| --desk-window-pad-x          | 14px         |
| --desk-window-pad-y          | 12px         |
| --desk-control-h             | 36px         |

### Timing

| Token             | Value  |
|-------------------|--------|
| --duration-micro  | 60ms   |
| --duration-short  | 120ms  |
| --duration-medium | 200ms  |
| --duration-long   | 320ms  |
| --duration-slow   | 500ms  |

### Focus ring

`box-shadow: 0 0 0 2px #0e0f13, 0 0 0 4px #a86e4a;`
or `outline: 2px solid #a86e4a; outline-offset: 2px;`

---

## 2. PER-SPECIES ANATOMY

### WINDOW CHROME (the desk window shell)

**Anatomy**: `.desk-window-shell` > `.desk-pullout-head` (title bar) + `.desk-surface-body` (scrolling content) + `.desk-surface-foot` (footer host).

**Shell**:
- `border: 1px solid #2a2e3e`; front window: `border-color: #363b50`
- `border-radius: 2px`
- `background: #15171d`
- `box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40), inset 0 0 0 1px #2a2e3e`
- `backdrop-filter: none`

**Title bar** (`.desk-pullout-head`):
- `height: 40px; padding: 0 12px; display: flex; align-items: center; gap: 10px;`
- Rest: `background: #1c1f27`; front: `background: #242833`
- `border-radius: 1px 1px 0 0` (radius - 1px)
- No border-bottom (tonal separation only)

**Window verbs** (minimize/maximize/close) in the head:
- Each verb: `aspect-ratio: 1; height: 100%; display: grid; place-items: center; border: 0; border-radius: 0; background: transparent; color: #9ba2b0;`
- Hover: `background: rgba(255,255,255,0.05); color: #f2f3f5;`
- Close verb hover: `background: #dc2626; color: #f2f3f5;`
- SVG icons: `width: 14px; height: 14px;`
- Last verb: `border-top-right-radius: 1px`

**Wings / Tab strip** (`.desk-wings` in the head):
- Container: `display: flex; align-items: center; margin-inline: auto;`
- Each tab (`.desk-wing`):
  - `border: 1px solid #2a2e3e; border-radius: 2px; background: rgba(255,255,255,0.035); color: #9ba2b0;`
  - `font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; padding: 4px 12px; cursor: pointer;`
  - Adjacent: `margin-left: -1px`
  - Hover: `color: #f2f3f5; background: rgba(255,255,255,0.05);`
  - Active (`.is-on`): `background: rgba(0,0,0,0.28); box-shadow: inset 1px 1px 0 rgba(0,0,0,0.30), inset -1px -1px 0 rgba(255,255,255,0.07); color: #f2f3f5;`
- Gear door: `padding: 4px 9px; font-size: 11px;` (same rules, glyph = `⚙︎`)

**Window body** (`.desk-surface-body`):
- `flex: 1; overflow: auto; padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 18px;`
- `container-type: inline-size; container-name: surface;`

---

### SurfaceVerbs

**Anatomy**: `div.surface-verbs` > `span.surface-verbs-status` + `span.surface-verbs-actions`.

**CSS**:
- `position: sticky; top: -12px;` (cancels body padding)
- `margin: -12px -14px 0;`
- `padding: 8px 14px;`
- `display: flex; align-items: center; gap: 8px;`
- `background: #15171d;` (window fill)
- `border-bottom: 1px solid #2a2e3e;`
- `z-index: 1;`

Status slot: `font-size: 12px; color: #9ba2b0; display: flex; align-items: center; gap: 6px;`
Actions slot: `display: flex; align-items: center; gap: 6px; margin-left: auto;`

---

### SurfaceSection

**Anatomy**: `div.surface-section` > `div.surface-section-head` > `h3` (label) + actions. Children below.

**CSS**:
- Section: `display: flex; flex-direction: column; gap: 6px; animation: surface-rise-in 200ms cubic-bezier(0.76,0,0.24,1) both;`
- Head: `display: flex; align-items: baseline; justify-content: space-between; gap: 8px; border-top: 1px solid rgba(255,255,255,0.035); padding-top: 8px;`
  - First section or after verbs: no border-top, no padding-top.
- Label (h3): `margin: 0; font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0;`
- Count badge: rendered as `span` text after the label.

---

### SurfaceRow / SurfaceRows

**Anatomy**: `ul.surface-rows` > `li.surface-row` > `div.surface-row-line` > glyph + text + meta + verbs.

**Rows container**: `list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px;`

**Row**: `border-radius: 2px; font-size: 13px;`
- Hover/focus-within: `background: rgba(255,255,255,0.035);`
- Selected (`[data-selected]`): `background: rgba(168,110,74,0.12);`

**Row line**: `min-height: 40px; display: flex; align-items: center; gap: 8px; padding: 4px 10px;`

**Row parts**:
- `.surface-row-glyph`: `flex-shrink: 0; width: 20px; text-align: center; color: #9ba2b0;`
- `.surface-row-text`: `flex: 1; min-width: 0; display: flex; flex-direction: column;`
  - `strong`: `font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
  - `small`: `color: #9ba2b0; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
- `.surface-row-meta`: `flex-shrink: 0; color: #9ba2b0; font-size: 12px; font-variant-numeric: tabular-nums;`
- `.surface-row-verbs`: `display: flex; align-items: center; gap: 4px; flex-shrink: 0; opacity: 0; transform: translateY(2px); transition: opacity 120ms, transform 120ms;`
  - On row hover/focus: `opacity: 1; transform: translateY(0);`
  - On `pointer: coarse`: always visible.

---

### SurfaceLedger / SurfaceLedgerRow

**Anatomy**: `div.surface-ledger` > `div.surface-ledger-head` (count + controls) + `ul.surface-ledger-rows` > `li.surface-ledger-row` > `button.surface-ledger-line` (grid) + `div.surface-ledger-open` (expanded detail).

**Ledger head**: `display: flex; align-items: center; gap: 8px; padding: 2px 4px 8px;`
- Count: `font: 600 12px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #f2f3f5;`

**Ledger line** (default 5-column grid):
- `display: grid; grid-template-columns: 52px minmax(0,1fr) max-content 6ch max-content; align-items: center; gap: 0 10px;`
- `width: 100%; min-height: 26px; padding: 2px 6px; border: 0; border-radius: 0; background: none; text-align: left;`
- `font: 12px "JetBrains Mono", ...; color: #f2f3f5; cursor: pointer;`
- Hover: `background: rgba(255,255,255,0.035);`
- Focus-visible: `background: rgba(255,255,255,0.035); outline: none; box-shadow: inset 0 0 0 1px #a86e4a;`
- Open row: `background: rgba(0,0,0,0.28); box-shadow: inset 1px 1px 0 rgba(0,0,0,0.30), inset -1px -1px 0 rgba(255,255,255,0.07);`

**Columns**:
- The 52px TIME column (`surface-ledger-time`): `color: #767e8d; font-variant-numeric: tabular-nums; white-space: nowrap;`
- Primary: `min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
- Cell: `color: #9ba2b0; font-size: 11px; white-space: nowrap;`
- Lead (selection mark): `flex: none;`

**Column templates** (via `data-cols`):
- `"facts"`: flex layout, no time column
- `"events"`: `52px max-content minmax(0,1fr)`
- `"meetings"`: `52px minmax(0,1fr) max-content max-content max-content`
- `"desk"`: flex layout
- `"crew"`: `minmax(0,5fr) minmax(0,4fr) max-content`

**Open detail**: `padding: 8px 10px 10px 68px; background: rgba(0,0,0,0.28); box-shadow: (etch);`

---

### SurfaceState

**Anatomy**: `div.surface-state` > `span.surface-state-glyph` + text + optional `button.surface-state-action`.

**CSS**: `display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 26px 12px; color: #9ba2b0; font-size: 13px; text-align: center;`
- Glyph: `font-size: 17px; opacity: 0.75;`
- Loading kind glyph pulses.
- Action button: `margin-top: 12px; border-color: #a86e4a; background: rgba(168,110,74,0.12);`

---

### SurfaceColumns / SurfaceSplit

**Columns**: `display: grid; gap: 18px; align-items: start;` Single column at narrow, `3fr 2fr` at >= 560px container.

**Split**: `display: grid; gap: 14px; align-items: start;` When open and wide: `1fr 1fr`.

---

### SurfaceWell / PaneWell

**SurfaceWell anatomy**: `div.surface-well` > `div.surface-well-head` (optional) + `div.surface-well-body`.

**Well**: `display: flex; flex-direction: column; min-width: 0; border-radius: 2px; background: rgba(0,0,0,0.28); box-shadow: inset 1px 1px 0 rgba(0,0,0,0.30), inset -1px -1px 0 rgba(255,255,255,0.07);`
- Head: `flex: none; padding: 6px 10px 4px; font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0; border-bottom: 1px solid rgba(255,255,255,0.06);`
- Body: `min-height: 0; max-height: 40cqh; overflow-y: auto; scrollbar-width: thin; padding: 6px 4px;`

**PaneWell** wraps an xterm or stripped pre inside `.terminal-well`:
- `background: #0f1115; box-shadow: (etch); border-radius: 2px; overflow: hidden;`

---

### SurfaceToggle

A thin wrapper around `CheckGadget` with `gap: 0`. No distinct visual -- it IS CheckGadget in a SurfaceSettingRow.

---

### SurfaceFacts

**Anatomy**: `dl.surface-facts` > `div` (display: contents) > `dt` + `dd`.

**CSS**: `margin: 0; display: grid; grid-template-columns: minmax(96px, max-content) minmax(0,1fr); gap: 3px 14px; font-size: 12px;`
- dt: `color: #9ba2b0;`
- dd: `margin: 0; overflow-wrap: anywhere;`

---

### MetricStrip

**Anatomy**: `div.surface-metrics` > `div` per metric > `strong` (value) + `small` (label).

**CSS**: `display: flex; flex-wrap: wrap; gap: 6px 18px;`
- strong: `font-size: 14px; font-variant-numeric: tabular-nums;`
- small: `color: #9ba2b0; font-size: 12px;`

---

### SurfaceFooter

**Anatomy**: `footer.surface-footer` > `div.surface-footer-layout` > egress + receipt + verbs.

**CSS**:
- Footer: `height: 36px; padding: 0 8px; background: #1c1f27; border-top: 1px solid #2a2e3e; box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40); flex-shrink: 0;`
- Layout: `display: grid; grid-template-columns: max-content minmax(0,1fr) max-content; align-items: center; height: 100%; gap: 6px;`
- Egress slot: `font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #767e8d; max-width: 156px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;`
- Receipt slot: `display: flex; justify-content: center; align-items: center; min-width: 0;`
  - Receipt line: `font: 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0;`
- Verbs slot: `display: flex; justify-content: flex-end; align-items: center; gap: 4px;`

At container <= 420px: reflows to 2-row grid: `"egress verbs" / "receipt receipt"`.

---

### Material

**Anatomy**: `div.surface-material` > headings (`strong.surface-material-h`), `p`, `ul`/`ol` > `li`.

**CSS**: `display: flex; flex-direction: column; gap: 6px; font-size: 13px; line-height: 1.55; color: #f2f3f5; overflow-wrap: anywhere;`
- Heading: `font-size: 15px; font-weight: 600; line-height: 1.4; margin-top: 4px;`
- Lists: `padding-left: 18px; gap: 3px;`
- Inline code: `font-family: "JetBrains Mono", ...; font-size: 0.92em; background: rgba(255,255,255,0.035); padding: 1px 5px; border-radius: 2px;`
- Links: `color: #a86e4a; text-decoration: none;` hover: `text-decoration: underline;`

---

### ConfirmVerb

**Anatomy**: Two-state button. Idle shows `label`; armed shows `confirmLabel` in danger tone. Click armed = confirm action.

Rendered as `Button variant="ghost" dense` (see Button below). The armed state adds `color: #f87171`.

---

### EditInPlace

**Anatomy**: A `button` (presented mode) or `textarea` (editing mode) with class `.surface-edit-in-place`.

**CSS**:
- Both: `font: inherit; color: inherit; text-align: inherit; background: none; border: 0; padding: 1px 4px; margin: -1px -4px; border-radius: 2px; max-width: 100%;`
- Button hover: `background: rgba(255,255,255,0.035); cursor: text;`
- Editing (`.is-editing`): `display: block; width: 100%; background: rgba(255,255,255,0.035); box-shadow: 0 0 0 1px #a86e4a; outline: none; resize: none;`

---

### Button (from Signal)

**Anatomy**: `button.btn.btn--{variant}` (+ `.btn--sm` for dense).

**Base** (`.btn`):
- `min-height: 28px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 4px 12px; border: 1px solid #2a2e3e; border-radius: 0;`
- `background: #1c1f27; box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40);`
- `color: #f2f3f5; font: 600 12px/1 "JetBrains Mono", ...; cursor: pointer;`
- Active: `transform: translateY(1px);`
- Focus-visible: `outline: 2px solid #a86e4a; outline-offset: 2px;`
- Disabled: `border-color: #2a2e3e; background: #15171d; box-shadow: none; color: #767e8d; cursor: not-allowed;`

**Dense** (`.btn--sm`): `min-height: 24px; padding-inline: 8px; font-size: 11px;`

**Primary** (`.btn--primary`):
- `border-color: #a86e4a; background: #a86e4a; color: #f2f3f5; box-shadow: inset 0 1px 0 rgba(255,255,255,0.22), 0 1px 2px rgba(0,0,0,0.3);`
- Hover: `background: #bc8058; border-color: #bc8058;`
- Active: `background: #936041;`

**Secondary** (`.btn--secondary` / default):
- `background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05); border-bottom-color: rgba(0,0,0,0.3); box-shadow: inset 0 1px 0 rgba(255,255,255,0.07);`
- Hover: `background: rgba(255,255,255,0.09);`

**Ghost** (`.btn--ghost`): `border-color: transparent; background: transparent;`
- Hover: `border-color: #a86e4a; background-color: #242833;`

**Danger** (`.btn--danger`): `border-color: #dc2626; background: #dc2626; color: #fff;`
- Hover: `background: #dc2626;` (danger-strong fallback same)

---

### desk-chip

**Anatomy**: `button.desk-chip` (or `a.desk-chip`). The `quiet` class mutes text; `is-primary` makes it accent-filled.

**CSS**:
- `height: 27px; padding: 0 12px; display: inline-flex; align-items: center; gap: 5px; line-height: 1; white-space: nowrap;`
- `border: 1px solid #2a2e3e; border-radius: 0; background: #1c1f27; color: #f2f3f5; font-size: 13px; cursor: pointer;`
- `box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40);`
- Hover: `border-color: #a86e4a; background: rgba(168,110,74,0.12);`
- Active: `transform: scale(0.94);`
- `.quiet`: `color: #9ba2b0;`
- `.is-primary`: `background: #a86e4a; border-color: #a86e4a; color: #f2f3f5; font-weight: 600; box-shadow: inset 0 1px 0 rgba(255,255,255,0.22);`
  - Hover: `background: #bc8058;`
- `[aria-pressed="true"]`: `border-color: #a86e4a; background: rgba(168,110,74,0.12); color: #f2f3f5;`

---

### GadgetGroup

**Anatomy**: `section.gadget-group` > `h4.gadget-group-label` (with engraved rule ::after) + `div.gadget-sheet`.

**Group**: `display: flex; flex-direction: column; margin-bottom: 12px;` (last: 0)
**Label**: `font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0; display: flex; align-items: center; gap: 8px;`
- `::after` (engraved rule): `content: ""; flex: 1; height: 2px; background: linear-gradient(rgba(0,0,0,0.30) 50%, rgba(255,255,255,0.07) 50%);`
**Sheet**: `display: flex; flex-direction: column;`

---

### GadgetRow

**Anatomy**: `div.gadget-row` > `span.gadget-row-label` (+ optional `.gadget-fact`) + `span.gadget-row-gadget`.

**CSS**:
- `display: grid; grid-template-columns: minmax(96px,200px) minmax(0,1fr); align-items: center; gap: 2px 10px; min-height: 26px; padding: 2px 6px;`
- Hover/focus-within: `background: rgba(0,0,0,0.28);`
- `[data-highlight]`: `background: rgba(168,110,74,0.12);`
- `[data-wide]`: `grid-template-columns: minmax(0,1fr);`
- Label: `font: 500 12px "JetBrains Mono", ...; color: #f2f3f5;`
- Fact: `font: 500 10px "JetBrains Mono", ...; color: #767e8d;`

---

### CheckGadget

**Anatomy**: `label.gadget-check` > hidden `input[checkbox]` + `span.gadget-check-well` > `svg`.

**Well**: `width: 16px; height: 16px; display: grid; place-items: center; border: 1px solid #2a2e3e; background: rgba(0,0,0,0.28); box-shadow: (etch);`
**SVG**: `width: 12px; height: 12px; stroke: #a86e4a; stroke-width: 2; fill: none; stroke-linecap: square;`
- Path: `d="M3.5 8.5 6.5 11.5 12.5 4.5"`
- Unchecked: `opacity: 0`; checked: `opacity: 1`
- Focus-visible: `border-color: #a86e4a;`

---

### CycleGadget

**Anatomy**: `span.gadget-cycle` > `span.gadget-cycle-glyph` ("↻") + native `select`.

**Select**: `appearance: none; min-height: 22px; padding: 2px 10px 2px 22px; border: 1px solid #2a2e3e; border-radius: 0; background: #1c1f27; background-image: none; box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40); color: #f2f3f5; font: 400 12px/1.35 "JetBrains Mono", ...; text-transform: uppercase; letter-spacing: 0.04em;`
- Hover: `background-color: #242833;`
- Active: box-shadow inverts (etch), `transform: translateY(1px);`

**Glyph**: `position: absolute; left: 7px; font: 11px "JetBrains Mono", ...; color: #9ba2b0;`

---

### StringGadget

**Anatomy**: `span.gadget-string` > `input` + `MicButton` (optional).

**Well**: `display: flex; align-items: stretch; width: 100%; min-height: 22px; border: 1px solid #2a2e3e; background: #15171d; box-shadow: (etch);`
- Focus-within: `border-color: #a86e4a;`

**Input**: `flex: 1; min-width: 0; min-height: 20px; border: 0; background: transparent; box-shadow: none; padding: 1px 6px; font: 400 12px/1.35 "JetBrains Mono", ...; color: #f2f3f5; text-align: left;`

**In-well mic**: `width: 20px; height: 20px; margin-right: 1px; border-radius: 0; border: 1px solid #2a2e3e; background: #1c1f27; box-shadow: inset 1px 1px 0 rgba(255,255,255,0.14), inset -1px -1px 0 rgba(0,0,0,0.40); font-size: 10px;`

---

### PadGadget

Same as StringGadget but uses `textarea` instead of `input`. Same well styling. Rows default to 3.

---

### FoldGadget

**Anatomy**: `details.gadget-fold` > `summary` > optional glyph + title + optional token. `div.gadget-fold-body`.

Uses native `<details>` semantics. Same visual as Disclosure (see below) but with the `<details>/<summary>` HTML pattern.

---

### StepperGadget

**Anatomy**: `span.gadget-string.gadget-stepper` > `input[type=number]` + optional unit span + `span.gadget-arrows` > two buttons.

Inherits StringGadget well. Arrows: `width: 14px; flex: none; display: flex; flex-direction: column; box-shadow: inset 1px 0 0 #2a2e3e;`
- Each arrow button: `flex: 1; padding: 0; border: 0; border-radius: 0; background: #1c1f27; box-shadow: (bevel); color: #9ba2b0; font-size: 6px; cursor: pointer;`
  - Hover: `color: #f2f3f5; background: #242833;`
  - Active: inverted bevel
  - Second button: `border-top: 1px solid #2a2e3e;`
- Unit: `font: 10px "JetBrains Mono", ...; color: #9ba2b0; padding: 0 5px;`

---

### PropGadget

**Anatomy**: `span.gadget-prop` > `input[type=range]` + `output.gadget-prop-read`.

**Track**: `height: 6px; border: 1px solid #2a2e3e; background: rgba(0,0,0,0.28) with 3 quartile ticks; box-shadow: (etch);`
**Thumb**: `width: 12px; height: 16px; border: 1px solid #2a2e3e; border-radius: 0; background: #242833; box-shadow: (bevel);`
**Read**: `width: 5ch; font: 12px "JetBrains Mono", ...; font-variant-numeric: tabular-nums; text-align: right; color: #f2f3f5;`

---

### GadgetTable

**Anatomy**: `div.gadget-table` > `div.gadget-table-head` + `div.gadget-table-row` (N) + optional `button.gadget-table-add`.

**Head/Row grid**: `grid-template-columns: repeat(N, minmax(0,1fr)) 24px; gap: 4px; align-items: center;`
**Head**: `min-height: 18px; padding: 0 2px; border-bottom: 1px solid #2a2e3e; box-shadow: 0 1px 0 rgba(255,255,255,0.07);`
- Spans: `font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0;`
**Row**: `min-height: 24px; padding: 1px 2px;` hover: `background: rgba(0,0,0,0.28);`
**Cell**: `font: 11px "JetBrains Mono", ...; color: #f2f3f5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
**Add button**: `min-height: 24px; margin-top: 3px; border: 1px dashed #2a2e3e; background: transparent; color: #9ba2b0; font: 600 11px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase;`

---

### LedMeter

**Anatomy**: `span.gadget-ledmeter` > `span.gadget-ledmeter-label` + `span.gadget-ledmeter-track` > N `span.gadget-ledmeter-seg`.

**Container**: `display: inline-flex; flex-direction: column; gap: 3px;`
**Label**: `font: 600 9px/1 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; color: #767e8d;`
**Track**: `display: inline-flex; gap: 2px; padding: 3px; border: 1px solid #2a2e3e; background: rgba(0,0,0,0.28); box-shadow: (etch);`
**Segment**: `width: 5px; height: 12px; background: rgba(255,255,255,0.05);`
- Lit: `background: #34d399;`
- Hot (>80%): `background: #fbbf24;`
- Scanning: one walking segment animated to `background: #a86e4a;`

---

### LampGadget

**Anatomy**: `span.gadget-lamp` > `span.gadget-lamp-dot` + text.

**Container**: `display: inline-flex; align-items: center; gap: 5px; font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #f2f3f5; white-space: nowrap;`
**Dot**: `width: 8px; height: 8px; border-radius: 0; background: rgba(255,255,255,0.05); box-shadow: 0 0 0 1px rgba(0,0,0,0.3);`
- on + ok: `background: #34d399;`
- on + warn: `background: #fbbf24;`
- on + fail: `background: #f87171;`
- off: text color becomes `#9ba2b0`

---

### TransportKey

**Anatomy**: `button.gadget-transport-key` > `span.gadget-transport-glyph` + `span.gadget-transport-word`.

**Key**: `width: 48px; height: 48px; display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; padding: 0;`
- `border: 1px solid #2a2e3e; border-radius: 0; background: #1c1f27; box-shadow: (bevel); color: #f2f3f5; font: 650 9px/1 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; cursor: pointer;`
- Glyph: `font-size: 16px; line-height: 1;`
- Hover: `background: #242833;`
- Active/pressed: `background: #a86e4a; color: #f2f3f5; border-color: #a86e4a; box-shadow: (inverted bevel = etch);`
- Danger tone: `color: #f87171; border-color: color-mix(in srgb, #f87171 45%, #2a2e3e);` active: `background: #f87171; color: #fff;`
- Compact (`[data-compact]`): `width: auto; min-width: 44px; height: 28px; flex-direction: row; gap: 5px; padding: 0 8px;` glyph: `font-size: 12px;`

---

### TransportRow

`span.gadget-transport-row` = `display: inline-flex; align-items: center; flex-wrap: wrap; gap: 6px;`

---

### EgressChip

**Anatomy**: `span.gadget-chip.gadget-chip-egress` (or `button` when clickable).

**CSS**: Inherits `.gadget-chip` base: `display: inline-flex; align-items: center; min-height: 18px; padding: 0 8px; border: 1px solid #2a2e3e; border-radius: 0; background: rgba(0,0,0,0.28); box-shadow: (etch); color: #767e8d; font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase;`
- Egress: `color: #34d399;` (default = local)
- `[data-scope="local"]`: `color: #34d399;`
- `[data-scope="mixed"]` or `"cloud"`: `color: #a86e4a;`
- Button variant: `cursor: pointer;`

---

### SecretRow

**Anatomy**: `div.gadget-secret` > `span.gadget-secret-label` + chip/StringGadget + `span.gadget-secret-verbs`.

**CSS**: `display: grid; grid-template-columns: minmax(96px,200px) minmax(0,1fr) auto; align-items: center; gap: 2px 10px; min-height: 26px; padding: 2px 6px;`
- Hover: `background: rgba(0,0,0,0.28);`
- Label: `font: 500 12px "JetBrains Mono", ...; color: #f2f3f5;` small: `font-size: 10px; color: #9ba2b0;`
- Chip `[data-set]`: `color: #a86e4a;` (shows "SET"); unset: `color: #767e8d;` (shows "---")

---

### StateChip

**Anatomy**: `span.surface-state-chip[data-state]` > `span.surface-state-chip-icon` + text.

**CSS**: `display: inline-flex; align-items: center; gap: 5px; min-height: 18px; padding: 0 8px; border: 1px solid #2a2e3e; border-radius: 0; background: rgba(0,0,0,0.28); box-shadow: (etch); font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; white-space: nowrap;`

**Icon**: `flex: none; font-size: 11px; line-height: 1;`

**State -> color map**:
| State       | Color     | Icon |
|-------------|-----------|------|
| idle        | `#9ba2b0` | `○`  |
| active      | `#a86e4a` | `●`  |
| working     | `#56c7f5` | `↻`  |
| success     | `#34d399` | `✓`  |
| warning     | `#fbbf24` | `⚠`  |
| failure     | `#f87171` | `✗`  |
| unreachable | `#767e8d` | `---` |

Working icon pulses: `animation: surface-chip-pulse 200ms ease-in-out infinite alternate;` (opacity 1 to 0.4).

---

### ProvenanceChip

**Anatomy**: `span.surface-provenance-chip` > `span.surface-provenance-source` + optional `span.surface-provenance-boundary` + optional inspect button.

**Chip**: Same geometry as StateChip/gadget-chip: `min-height: 18px; padding: 0 8px; border: 1px solid #2a2e3e; border-radius: 0; background: rgba(0,0,0,0.28); box-shadow: (etch); font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; color: #9ba2b0;`

**Boundary badge**: `display: inline-flex; align-items: center; padding: 0 4px; min-height: 14px; background: rgba(168,110,74,0.12); border: 1px solid rgba(255,255,255,0.06); font-size: 9px; letter-spacing: 0.06em; color: #a86e4a;`

---

### Receipt

**Anatomy**: `span.surface-receipt[data-status]` > `span.surface-receipt-lamp` + `span.surface-receipt-label` + optional `span.surface-receipt-time` + optional inspect button.

**Container**: `display: inline-flex; align-items: center; gap: 5px; font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #9ba2b0;`
**Lamp**: `width: 6px; height: 6px; flex: none;`
- ok: `background: #34d399;`
- warn: `background: #fbbf24;`
- danger: `background: #f87171;`
**Time**: `color: #767e8d; font-variant-numeric: tabular-nums;`

---

### ActionNotice

**Anatomy**: `div.surface-action-notice[data-tone]` > optional icon + `div.surface-action-notice-body` + optional `button.surface-action-notice-btn`.

**Container**: `display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px; border: 1px solid #2a2e3e; border-radius: 2px; background: #1c1f27; font: 13px "JetBrains Mono", ...; color: #f2f3f5;`

**Tone backgrounds**:
| Tone   | background                      | border-color |
|--------|---------------------------------|--------------|
| ok     | `rgba(52,211,153,0.12)`         | `#34d399`    |
| warn   | `rgba(251,191,36,0.12)`         | `#fbbf24`    |
| danger | `rgba(248,113,113,0.12)`        | `#f87171`    |
| info   | `rgba(86,199,245,0.12)`         | `#56c7f5`    |

**Action button**: `min-height: 27px; padding: 0 12px; border: 1px solid #2a2e3e; border-radius: 0; background: #1c1f27; box-shadow: (bevel); color: #f2f3f5; font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.04em; text-transform: uppercase;`

---

### Disclosure

**Anatomy**: `div.surface-disclosure[data-open]` > `button.surface-disclosure-trigger` > `span.surface-disclosure-caret` ("▸") + `span.surface-disclosure-label` + optional `span.surface-disclosure-token`. `div.surface-disclosure-body` (when open).

**Trigger**: `display: flex; align-items: center; gap: 6px; width: fit-content; min-height: 26px; margin: 2px 0; padding: 2px 9px 2px 7px; border: 0; border-radius: 2px; background: transparent; font-size: 12px; font-weight: 600; color: #9ba2b0; cursor: pointer;`
- Hover: `background: rgba(255,255,255,0.035); color: #f2f3f5;`

**Caret**: `font-size: 11px; color: #9ba2b0; transition: transform 120ms;`
- Open: `transform: rotate(90deg);`

**Token**: `margin-left: auto; font: 10px "JetBrains Mono", ...; letter-spacing: 0.06em; color: #767e8d;`

**Body**: `padding: 4px 8px 8px; display: flex; flex-direction: column; gap: 8px;`

**RAW variant**: trigger becomes mono section-label style: `font-family: "JetBrains Mono", ...; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #767e8d;`

---

### ProgressPlan

**Anatomy**: `div.surface-progress-plan` > `div.surface-plan-steps` (list) > step divs > `div.surface-plan-step[data-status]` > icon + label + optional progress bar + optional rate. Optional `div.surface-plan-footer`.

**Container**: `display: flex; flex-direction: column; gap: 2px; font: 12px "JetBrains Mono", ...; color: #f2f3f5;`

**Step**: `display: flex; align-items: center; gap: 6px; min-height: 24px; padding: 2px 6px;`

**Step state colors**:
| Status  | Color     | Icon |
|---------|-----------|------|
| queued  | `#9ba2b0` | `○`  |
| running | `#56c7f5` | `●`  |
| done    | `#34d399` | `✓`  |
| failed  | `#f87171` | `✗`  |

**Icon**: `width: 14px; text-align: center; font-size: 11px; line-height: 1;` Running pulses (opacity 1 to 0.35).
**Label**: `flex: 1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`
**Rate**: `font-size: 10px; color: #767e8d; font-variant-numeric: tabular-nums; letter-spacing: 0.04em;`

**Progress bar**: `width: 48px; height: 6px; border: 1px solid #2a2e3e; background: rgba(0,0,0,0.28); box-shadow: (etch); overflow: hidden;`
- Fill: `height: 100%; background: #56c7f5;` (done: `#34d399`, failed: `#f87171`)

**Compact**: min-height 20px, detail hidden.

---

### ChoiceCardGroup / ChoiceCard / ChoiceCardShell

**Group**: `display: flex; flex-direction: column; gap: 2px;`
- `layout="row"`: `display: grid; grid-template-columns: repeat(N, minmax(0,1fr)); align-items: start; max-width: 1240px;` Stacks at container < 760px.

**Card** (`.surface-choice-card`): `position: relative; display: flex; flex-direction: column; gap: 6px; padding: 12px 12px 8px; border: 1px solid #2a2e3e; border-radius: 2px; background: #15171d; cursor: pointer;`
- Hover: `background: rgba(255,255,255,0.04);`
- Selected: `border-color: #a86e4a; background: rgba(168,110,74,0.12); box-shadow: 0 0 0 1px rgba(168,110,74,0.4), 0 4px 18px rgba(168,110,74,0.28);`
- Recommended: `background: linear-gradient(180deg, rgba(168,110,74,0.12), transparent 42%), #15171d; border-color: #a86e4a;`
  - `::after` badge: `content: "RECOMMENDED"; position: absolute; top: -1px; right: 8px; padding: 2px 7px; border: 1px solid #a86e4a; border-top: 0; background: #a86e4a; font: 700 9px/1.2 "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; color: #f2f3f5;`
- Disabled: `opacity: 0.55; cursor: not-allowed;`

**Tier temperature** (via `data-tier`):
- `[data-tier]`: `border-top: 2px solid var(--choice-tier);` padding-top adjusts -1px.
- light: `--choice-tier: #5b8def`
- balanced: `--choice-tier: #a86e4a`
- full: `--choice-tier: #bc8058`

**Head**: `display: flex; align-items: center; gap: 8px;`
- Emblem: `font-size: 15px; line-height: 1; color: tier color or #767e8d;`
- Label: `font: 700 13px "JetBrains Mono", ...; letter-spacing: 0.02em; color: #f2f3f5;`

**Description**: `font: 12px "JetBrains Mono", ...; color: #9ba2b0; line-height: 1.35;`
**Summary**: `font: 600 12px "JetBrains Mono", ...; color: #f2f3f5; line-height: 1.45; padding: 6px 8px; border-left: 2px solid tier-color; background: #1c1f27; border-radius: 0 2px 2px 0;`
**Facts**: `display: flex; flex-wrap: wrap; gap: 4px;` each fact chip: `padding: 2px 7px; border: 1px solid #2a2e3e; border-radius: 2px; background: #1c1f27; font: 11px "JetBrains Mono", ...;`
  - key: `color: #767e8d; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600;`
  - val: `color: #9ba2b0; font-variant-numeric: tabular-nums;`

**Confirm button**: `min-height: 27px; padding: 0 16px; margin-top: 4px; border: 1px solid #a86e4a; border-radius: 0; background: #a86e4a; color: #f2f3f5; font: 600 10px/1 "JetBrains Mono", ...; letter-spacing: 0.04em; text-transform: uppercase; cursor: pointer; align-self: flex-end;`

---

### Popover

**Anatomy**: Portal: `div.surface-popover-backdrop` + `div.surface-popover`.

**Backdrop**: `position: fixed; inset: 0; z-index: 81; background: transparent;`
**Popover**: `position: absolute; z-index: 82; min-width: 120px; max-width: 320px; padding: 8px; border: 1px solid #2a2e3e; border-radius: 2px; background: #1c1f27; box-shadow: (etch); color: #f2f3f5; font: 12px "JetBrains Mono", ...;`

---

### MicButton

**Anatomy**: `button.desk-mic` (square) > `span` > `img` (pixelated 16x16 sprite).

**Default (in-field)**: `width: 34px; height: 34px; border-radius: 2px; border: 1px solid #2a2e3e; background: #1c1f27; font-size: 15px; cursor: pointer; display: inline-grid; place-items: center;`
- Listening: `border-color: #a86e4a; animation: pulse 1.5s ease-in-out infinite;`
- Busy: `opacity: 0.7;`
- Failed: `border-color: #f87171;`
- Unsupported: `opacity: 0.45; cursor: not-allowed;`

**In-well mic** (inside StringGadget): `width: 20px; height: 20px; margin-right: 1px; border-radius: 0; border: 1px solid #2a2e3e; background: #1c1f27; box-shadow: (bevel); font-size: 10px;`

**Transport variant** (`.desk-mic.gadget-transport-key`): takes TransportKey's 48x48 form with "Talk" word.

The mic face renders a 16x16 pixelated sprite image, not an SVG. States use different sprite sources.

---

### CitationChips

**Anatomy**: `div.surface-citations` > `button.desk-chip.quiet` per citation.

Each chip: standard desk-chip `.quiet` variant (see above). Text follows `Kind . id` format.

---

### DoorBoardLane scroll hint

**Anatomy**: `div.door-board-hint-wrap[data-scroll-hint]` wrapping `div.door-board-viewport`.

**Hint wrapper**: `position: relative;`
- `::before` (left fade): `content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 28px; display: none; pointer-events: none; z-index: 1; background: linear-gradient(to right, #15171d, transparent);`
- `::after` (right fade): same but `right: 0; background: linear-gradient(to left, #15171d, transparent);`
- `[data-scroll-hint="right"]::after`: `display: block;`
- `[data-scroll-hint="left"]::before`: `display: block;`
- `[data-scroll-hint="both"]`: both `display: block;`

---

### SurfaceStream / SurfaceStreamDay / SurfaceStreamEntry

**Stream**: `display: flex; flex-direction: column;`
**Day label**: `font: 600 10px "JetBrains Mono", ...; letter-spacing: 0.06em; text-transform: uppercase; color: #767e8d; padding: 14px 4px 6px;` with `::after` hairline rule.
**Entry**: `display: grid; grid-template-columns: 48px minmax(0,1fr); gap: 0 12px; padding: 8px 10px 10px; border-radius: 2px;`
- When (time column): `text-align: right; color: #767e8d; font: 12px "JetBrains Mono", ...; font-variant-numeric: tabular-nums;`
- Said (text): `font-size: 15px; font-weight: 480; line-height: 1.4;`
- Meta: `font-size: 12px; color: #9ba2b0;`

---

### SurfaceTraffic / SurfaceTrafficTurn

**Traffic**: wraps a SurfaceWell. Body: `flex: 1; gap: 10px; padding: 8px 10px;`
**Turn**: `display: grid; grid-template-columns: max-content minmax(0,1fr); gap: 2px 8px; font: 12px "JetBrains Mono", ...; line-height: 1.5;`
- Prefix: `font-weight: 700; letter-spacing: 0.04em; color: #9ba2b0; max-width: 16ch; overflow: hidden; text-overflow: ellipsis;`
- Text: `white-space: pre-wrap; word-break: break-word; color: #f2f3f5;`
- Error: prefix and text become `color: #f87171;`

---

### SurfaceGroup / SurfaceSettingRow

**Group**: `border-top: 1px solid rgba(255,255,255,0.06); border-radius: 0; background: none;`
**Setting row**: `display: flex; align-items: center; gap: 10px; min-height: 36px; padding: 5px 12px;` + hairline between rows. Hover: `background: rgba(0,0,0,0.28);`
- Icon: `16px square; color: #9ba2b0;`
- Text: `strong: font-weight: 500; font-size: 13px;` `small: color: #9ba2b0; font-size: 12px;`
- Control: `flex: none; max-width: 46%; justify-content: flex-end;`

---

### SurfaceLibrary / SurfaceLibraryTile / SurfaceLibraryGhost

**Library grid**: `display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;`

**Tile**: `display: flex; flex-direction: column; border-radius: 2px; overflow: hidden; background: rgba(255,255,255,0.035); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06); min-height: 150px;`
- Face: `flex: 1; padding: 11px 12px 8px; background: rgba(0,0,0,0.28); font: 11px "JetBrains Mono", ...; line-height: 1.55; color: #9ba2b0; white-space: pre-wrap; max-height: 120px; overflow: hidden;`
  - Bottom hairline via `::after`.
- Spine: `padding: 9px 12px 11px; display: flex; flex-direction: column; gap: 6px;`

**Ghost tile**: `border: 1.5px dashed #2a2e3e; background: none; box-shadow: none;` Center-aligns a + icon and text.

---

### SurfaceSwitchboard / SurfaceBay

**Grid**: `display: grid; gap: 10px;` 1 col narrow, 2 cols at >= 560px container.

**Bay**: `display: flex; align-items: stretch; gap: 12px; padding: 13px 15px; border-radius: 2px; background: rgba(255,255,255,0.035); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);`
- Route bay: `background: rgba(168,110,74,0.12); box-shadow: inset 0 0 0 1px rgba(168,110,74,0.12);`
- Tag: `font: 700 10px "JetBrains Mono", ...; letter-spacing: 0.08em; text-transform: uppercase; color: #a86e4a; background: rgba(168,110,74,0.12); padding: 2px 8px;`

---

### SurfaceWings

Documented above under Window Chrome > Wings / Tab strip.

---

## 3. ICONS (SVG path data)

### StateChip / ProgressPlan default icons

These are unicode text, not SVG paths:
- idle / queued: `○` (U+25CB CIRCLE)
- active / running: `●` (U+25CF BLACK CIRCLE)
- working: `↻` (U+21BB CLOCKWISE ARROW)
- success / done: `✓` (U+2713 CHECK MARK)
- warning: `⚠` (U+26A0 WARNING SIGN)
- failure / failed: `✗` (U+2717 BALLOT X)
- unreachable: `---` (U+2014 EM DASH)

### CheckGadget SVG

```
<svg viewBox="0 0 16 16">
  <path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="#a86e4a" stroke-width="2" fill="none" stroke-linecap="square"/>
</svg>
```

### CycleGadget glyph

`↻` (unicode, not SVG)

### Disclosure caret

`▸` (U+25B8 BLACK RIGHT-POINTING SMALL TRIANGLE). Rotates 90deg when open.

### Gear door

`⚙︎` (U+2699 GEAR + VS15)

### MicButton

The mic renders a 16x16 pixelated SPRITE IMAGE (not SVG). The system sprite URLs are generated at build time. For mockups, use a 16x16 placeholder or a simple mic SVG icon.

### Window verb SVGs

`width: 14px; height: 14px;` -- minimize (horizontal line), maximize (square), close (X). Exact paths are in the DeskWindowFrame component, not in the surface library.

---

## 4. THE JIRA WIZARD OUTLINE (reference composition)

Source: `web/src/features/project-room/setup/JiraWizard.tsx`

**Import list from the surface barrel**:
ChoiceCard, ChoiceCardGroup, ChoiceCardShell, StateChip, ProvenanceChip, Receipt, ActionNotice, ProgressPlan, SurfaceLedger, SurfaceLedgerRow, SurfaceWell, GadgetGroup, GadgetRow, CheckGadget, StringGadget, LampGadget, TransportKey.

**Feature CSS** (`jira-wizard.css`): layout only, zero species restyling.

### Step D1: Accounts (`JiraAccountsStep`)

Top to bottom:
1. **ChoiceCardGroup** (layout="row", name="jira-account")
   - Per connection: **ChoiceCard** with:
     - label = site name, summary = email, emblem = site initial letter, tier = ok/warn
     - Children: inline row of **StateChip** + **ProvenanceChip** + recheck button
     - fold (if needs auth): **SurfaceWell** containing the login command + **TransportKey** (compact, glyph="C", word="Copy")
   - Known-to-acli cards: **ChoiceCardShell** (not radio, just visual) with StateChip + action button
   - Ghost add card: **ChoiceCardShell** with dashed border + two **StringGadget**s (Site, Email) + Add button
2. **Footer**: **LampGadget** ("N of M connected") + spacer + Back button + primary Next button

### Step D2: Scope (`JiraScopeStep`)

Top to bottom:
1. **ChoiceCardGroup** (layout="row") for project selection -- each **ChoiceCard** with emblem=project key, facts chips, **ProvenanceChip**
2. **GadgetGroup** ("ISSUE TYPES") with **GadgetRow**s containing **CheckGadget** toggles
3. **GadgetGroup** ("STATUS CATEGORIES") with **CheckGadget** toggles
4. **GadgetRow** for custom JQL with **StringGadget**
5. Preview **ActionNotice** (info tone) if no preview yet; or preview results with big count + **SurfaceLedger** of matching issues (**SurfaceLedgerRow**s)
6. **Footer**: **LampGadget** + spacer + Back + Test buttons

### Step D3: Test (`JiraTestStep`)

Top to bottom:
1. **ProgressPlan** with steps: discover-connection, discover-projects, discover-types, discover-statuses, search-issues
2. Status **ActionNotice** (ok/warn/danger tone) showing results or errors
3. If successful: results **SurfaceLedger** with issue rows
4. **Footer**: **LampGadget** + spacer + Back + Accept buttons

---

## SURPRISES

1. **Material has no dedicated CSS file** -- its styles live inside `surface.css` under `.surface-material`.

2. **ConfirmVerb has no CSS** -- it renders two `Button variant="ghost" dense` states in sequence. The armed state applies `style={{ color: "var(--danger-signal)" }}` inline in the component (Surface.tsx:~1110). No `.surface-confirm-*` class exists.

3. **SurfaceToggle has no CSS** -- it is literally `<CheckGadget>` with a wrapper div that has `gap: 0`. The class `.surface-toggle` exists in surface.css but only sets `gap: 0`.

4. **MicButton is NOT SVG** -- it renders a pixelated 16x16 PNG sprite image from a build-time sprite sheet (`SYSTEM.micGlyph`). Mockup authors will need to substitute their own mic icon.

5. **Button CSS lives in `web/src/styles/global.css`**, not in the desk CSS files. The `.btn` rules use `:where()` for low specificity. The desk-era overrides in `global.css:616-627` re-skin `.btn--secondary` with the gleam/shade system.

6. **The surface library's SurfaceCode** (`pre.surface-code`) has styling in surface.css but no dedicated component export beyond a thin wrapper.

7. **The `--font-size-sm` token (0.8125rem = 13px) equals `--desk-surface-body-size`** -- these are the same value. Similarly `--font-size-xs` (0.75rem = 12px) equals `--desk-surface-detail-size`.

8. **All radii are 2px** -- even `--radius-pill`. The design explicitly killed Apple-round corners. The only exception is `--desk-inlet-radius: 6px` (compact reference picker) and `--desk-sheet-top-radius: 18px` (phone sheet grip).

9. **No Gaussian shadows on windows** -- `--desk-window-shadow: none`. Depth is entirely from bevels (inset 1px highlights/shadows). The only real shadow is `--elev-1` for very rare uses.

10. **The JiraWizard uses zero feature CSS restyling** -- all visual identity comes from the surface library. Its `jira-wizard.css` is 67 lines of pure layout (gaps, grid, footer alignment). This validates the library as self-sufficient for composition.

11. **TopologySurface and SurfaceWings** are in the barrel but TopologySurface is a canvas/SVG graph renderer (not a styling species) and SurfaceWings is window chrome (documented above under Wings).

12. **The `desk-chip` is NOT in the surface barrel** -- it lives in `chrome-menus.css` as part of the desk chrome layer. CitationChips uses it directly. Mockup authors need both the surface library species AND the `desk-chip` rules.
