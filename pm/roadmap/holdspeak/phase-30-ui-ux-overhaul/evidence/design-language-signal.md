# "Signal" — HoldSpeak design language (HS-30-02)

**Date:** 2026-06-01. **Status: DRAFT — awaiting Karol's sign-off.** No token is
written (HS-30-03) until this is approved.

The visual language that replaces the Amiga Workbench skin. Dark-only, bold,
distinctive — a calm-but-confident real-time-monitor surface for a local, private
voice tool. Derived with the `ui-ux-pro-max` skill (output captured below) and
adapted to Karol's locked seeds.

**See it:** `evidence/signal-preview.png` — a static mock embodying every token in
this doc (nav, hero, transcript panel, intel rail, buttons, status pills, focus
ring, palette swatches), rendered from `evidence/signal-preview.html`. Compare it
against `evidence/before/before-runtime.png`.

## 0. Skill grounding (captured)

- **Style → Dark Mode (OLED):** *high contrast, deep black, eye-friendly; WCAG AAA;
  best for coding platforms / dev tools.* Anti-patterns: light-mode default, slow.
- **Pattern → Real-Time / Operations:** *dark/neutral, status colours
  (green/amber/red), data-dense but scannable.* Matches the Runtime monitor.
- **Typography → Space Grotesk + Inter + JetBrains Mono (tri-stack):* *Space
  Grotesk 600–700 headings (geometric, technical character); Inter 400–600 body/UI
  (legibility); JetBrains Mono 500 for data/stats.* Exactly the chosen trio.
- **Color (dev-tool dark):** skill ships a slate-900 base + green accent; **we keep
  its structural ramp (bg / surface / muted / border / foreground / muted-fg) but
  swap the cool slate base for Karol's neutral near-black and the green accent for
  the signature orange.**

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "bold distinctive dark developer productivity tool, near-black, orange accent, confident, real-time monitor" \
  --design-system -p "HoldSpeak Signal" -f markdown
# + --domain typography / --domain color (dark + orange). Full output in the turn log.
```

## 1. Identity in one line

**Signal = signature orange on a near-black, layered surface, technical-geometric
type, real depth, one calm pulse.** The orange is the *signal* — reserved for the
live/primary moment, never decoration.

## 2. Palette

Neutral near-black ramp (not slate-blue), elevation by lightness. All contrast
ratios below are computed against the app canvas `--bg` (#0E0F13, relative
luminance ≈ 0.0048) unless noted; target is WCAG **AA** (4.5:1 text / 3:1
large+non-text), AAA where marked.

### Surfaces (elevation by lightness)
| Token | Hex | Role |
|---|---|---|
| `--bg` | `#0E0F13` | App canvas (deepest) |
| `--surface-1` | `#15171D` | Cards / panels (raised) |
| `--surface-2` | `#1C1F27` | Popovers, dropdowns, drawer, modals |
| `--surface-3` | `#242833` | Top layer: command palette, tooltips |
| `--surface-hover` | `rgba(255,255,255,0.04)` | Hover overlay on any surface |
| `--surface-active` | `rgba(255,255,255,0.07)` | Pressed/active overlay |

> Seed note: Karol's "raised #1A1C22" sits between `--surface-1` and `--surface-2`;
> the ramp keeps that warmth while giving three clean elevation steps.

### Text
| Token | Hex | Contrast vs `--bg` | Role |
|---|---|---|---|
| `--text` | `#F2F3F5` | **≈17:1** (AAA) | Primary text |
| `--text-muted` | `#9BA2B0` | **≈7.1:1** (AAA) | Secondary text, labels |
| `--text-faint` | `#767E8D` | **≈4.7:1** (AA) | Hints, placeholders, meta |
| `--text-on-accent` | `#0E0F13` | **≈6.8:1** on orange | Ink on the orange fill |

> **Hard rule:** never white text on the orange fill (≈2.5:1 — fails). The orange
> always carries **dark** ink (`--text-on-accent`).

### Accent (the signal)
| Token | Hex / value | Contrast vs `--bg` | Role |
|---|---|---|---|
| `--accent` | `#FF6B35` | **≈6.8:1** (AA, large+normal) | Primary action, live, focus |
| `--accent-hover` | `#FF7D4D` | — | Hover on accent surfaces |
| `--accent-press` | `#EC5A28` | — | Pressed accent |
| `--accent-tint` | `rgba(255,107,53,0.12)` | — | Selected/active fills, chips |
| `--accent-glow` | `rgba(255,107,53,0.28)` | — | Glow shadow on primary/live |

### Status (dark-tuned; always paired with an icon, never colour alone)
| Token | Hex | Contrast | Role |
|---|---|---|---|
| `--ok` | `#34D399` | ≈9:1 | Success / done / connected |
| `--warn` | `#FBBF24` | ≈11:1 | Warning / stale / queued |
| `--danger` | `#F87171` | ≈6:1 | Error / failed (text/icon) |
| `--danger-fill` | `#DC2626` | white ink ≈4.9:1 | Destructive button fill |
| `--info` | `#56C7F5` | ≈8:1 | Info / running / neutral status |

### Lines
| Token | value | Role |
|---|---|---|
| `--border-subtle` | `rgba(255,255,255,0.08)` | Hairline dividers |
| `--border` | `rgba(255,255,255,0.12)` | Default card/input border |
| `--border-strong` | `rgba(255,255,255,0.20)` | Emphasis / hovered field |

## 3. Typography

Tri-stack (skill-recommended). Fonts via `@fontsource`: `space-grotesk`, `inter`,
`jetbrains-mono`. VT323 + Sora are removed.

| Token | Font / weight | Size / line-height / tracking | Use |
|---|---|---|---|
| `--type-display` | Space Grotesk 700 | 32 / 1.15 / −0.02em | Page `h1` hero |
| `--type-h1` | Space Grotesk 600 | 24 / 1.2 / −0.01em | Route title |
| `--type-h2` | Space Grotesk 600 | 18 / 1.3 / −0.005em | Panel title |
| `--type-eyebrow` | Inter 600 | 12 / 1.3 / +0.06em **uppercase** | Kicker / panel label |
| `--type-body` | Inter 400 | 14 / 1.5 / 0 | Default UI/body text |
| `--type-body-lg` | Inter 400 | 16 / 1.55 / 0 | Lead paragraphs |
| `--type-label` | Inter 500 | 13 / 1.4 / 0 | Form labels, nav |
| `--type-data` | JetBrains Mono 500 | 13 / 1.4 / 0 | Timers, counts, IDs, stats |
| `--type-code` | JetBrains Mono 400 | 12.5 / 1.6 / 0 | YAML / code / dry-run trace |

The **uppercase tracked eyebrow** replaces the old pixel-font "title strip" idiom —
it gives technical character (Space Grotesk + Mono data) without the VT323 toy
feel. Headings stay sequential `h1→h2→h3` (audit problem #12).

## 4. Depth (real elevation — replaces all-`none`)

Dark-on-dark, so elevation = surface-lightness step **+** a soft black shadow **+** a
1px top inner highlight. Accent carries a glow only on the live/primary moment.

| Token | value |
|---|---|
| `--elev-1` (card) | `0 1px 2px rgba(0,0,0,.40), inset 0 1px 0 rgba(255,255,255,.04)` |
| `--elev-2` (popover/drawer) | `0 8px 24px rgba(0,0,0,.50)` |
| `--elev-3` (modal) | `0 16px 48px rgba(0,0,0,.60)` |
| `--glow-accent` | `0 0 0 1px rgba(255,107,53,.40), 0 4px 18px var(--accent-glow)` |

## 5. Shape (real radius — replaces all-`0`)

| Token | value | Use |
|---|---|---|
| `--radius-xs` | 4px | Tiny chips, dots |
| `--radius-sm` | 6px | Inputs, small buttons, pills-square |
| `--radius-md` | 10px | Buttons, cards (default) |
| `--radius-lg` | 14px | Panels, modals, drawer |
| `--radius-pill` | 999px | Status pills, toggles |

## 6. Motion

| Token | value | Use |
|---|---|---|
| `--ease-standard` | `cubic-bezier(0.16, 1, 0.3, 1)` | The "Signal" settle — most transitions |
| `--ease-emphasized` | `cubic-bezier(0.2, 0, 0, 1)` | Enter/exit of overlays |
| `--dur-fast` | 120ms | Hover, press |
| `--dur-base` | 200ms | Default transition |
| `--dur-slow` | 320ms | Modals, drawer, route affordances |

- **Press:** `scale(0.98)` + `--dur-fast`. **Hover:** `--surface-hover` lift, `--dur-fast`.
- **The one brand motion:** a gentle accent **pulse** on the live indicator (and the
  active "recording" dot). Everything else is restrained.
- **`prefers-reduced-motion: reduce`** disables transforms, the pulse, and the glow
  animation — opacity-only fallbacks. (Skill checklist + a11y story HS-30-09.)

## 7. Focus & states

- **Focus ring** (visible on dark): `0 0 0 2px var(--bg), 0 0 0 4px var(--accent)`
  — a 2px gap then a 2px orange ring. Applied to every interactive element.
- **Disabled:** drop to `--text-faint` + `--surface-1`, **no** diagonal hatch
  (retire the Workbench hatch artifact); cursor `not-allowed`.
- **Selected/active:** `--accent-tint` fill + `--accent` left-marker or text, **plus**
  a non-colour cue (weight/icon) per the *Color Only* rule.

## 8. Density

Two modes only (already in the component API):
- **comfortable** (default): spacing scale base, `--type-body` 14px.
- **dense** (rail, data tables, dry-run trace): tighter spacing step, `--type-data`
  for figures. Spacing rhythm stays on the 4px base
  (`2,4,8,12,16,20,24,32,40,48,64`).

## 9. Token-name map (Signal → `tokens.css`, for HS-30-03)

HS-30-03 is a mechanical translation: delete every `--wb-*` and write these
semantic tokens (components keep reading from `tokens.css`).

- Canvas/surfaces → `--bg`, `--surface-1..3`, `--surface-hover`, `--surface-active`
- Text → `--text`, `--text-muted`, `--text-faint`, `--text-on-accent`
- Accent → `--accent`, `--accent-hover`, `--accent-press`, `--accent-tint`, `--accent-glow`
- Status → `--ok`, `--warn`, `--danger`, `--danger-fill`, `--info`
- Lines → `--border-subtle`, `--border`, `--border-strong`
- Depth → `--elev-1..3`, `--glow-accent`
- Shape → `--radius-xs/sm/md/lg/pill`
- Type → `--font-display` (Space Grotesk), `--font-ui` (Inter), `--font-mono`
  (JetBrains Mono) + the `--type-*` role tokens in §3
- Motion → `--ease-standard`, `--ease-emphasized`, `--dur-fast/base/slow`
- Focus → `--focus-ring`

Old → new quick map: `--wb-blue`→retired (no blue desktop); `--wb-black`/desktop→
`--bg`; white panels→`--surface-1`; `--wb-orange`→`--accent`; hard hairlines→
`--border-subtle`; `--radius-*: 0`→the §5 scale; `--elevation-*: none`→§4.

## 10. AA contrast summary (verified targets — re-checked for real in HS-30-09)

| Pairing | Ratio | Verdict |
|---|---|---|
| `--text` on `--bg` | ≈17:1 | AAA |
| `--text-muted` on `--bg` | ≈7.1:1 | AAA |
| `--text-faint` on `--bg` | ≈4.7:1 | AA (hints/non-essential) |
| `--accent` on `--bg` | ≈6.8:1 | AA |
| `--text-on-accent` (dark ink) on `--accent` | ≈6.8:1 | AA |
| white on `--accent` | ≈2.5:1 | **FORBIDDEN** |
| `--ok` / `--warn` / `--info` on `--bg` | ≈9–11:1 | AAA |
| `--danger` on `--bg` | ≈6:1 | AA |

## Sign-off

- [x] **Karol approves "Signal"** as the design language for Phase 30.

2026-06-01 — **Approved by Karol** ("yea dude this looks a lot better") against
`evidence/signal-preview.png`. HS-30-03 (foundation tokens) is unblocked.
