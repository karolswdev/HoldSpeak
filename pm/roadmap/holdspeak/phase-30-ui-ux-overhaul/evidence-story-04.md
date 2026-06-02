# HS-30-04 Evidence — Navigation + layout shell

**Date:** 2026-06-01.
**Story:** [story-04-nav-and-layout-shell.md](./story-04-nav-and-layout-shell.md).

## Implementation Evidence

The shared shell is rebuilt to the IA spec (`evidence/ia-spec.md` §1–§3) on the
Signal foundation. Every route inherits it.

**`web/src/components/TopNav.astro`** — the flat 5-link strip is replaced by a
**grouped** model with section labels + dividers:
- **Live** → Runtime · **Review** → History, Activity · **Configure** →
  Dictation, Companion.
- Brand (AppMark + "HoldSpeak" in Space Grotesk, accent mark with a glow) → Runtime.
- Active route is **dual-encoded** (skill `ux`/*Color Only*): `--accent-tint`
  fill + weight 600 + an accent underbar + `aria-current="page"`.
- Right cluster: the `status` slot (default `LocalPill`) + a **⚙ Settings** button
  (`[data-settings-open]`, `aria-haspopup="dialog"`).
- The VT323 font-hack + `flex-wrap` pile-up are gone; below 880px the groups
  collapse behind a **menu toggle** (`[data-nav-toggle]`, `aria-expanded`).

**`web/src/layouts/AppLayout.astro`** — owns the **global Settings drawer** (IA
§2: Settings lifted out of History into a shell-level drawer):
- A right-side slide-over (`role="dialog"`, `aria-modal`, `--surface-2`,
  `--elev-3`) over a dimmed backdrop; opens from the ⚙, closes on the ✕, backdrop
  click, or `Escape`; focus moves into the drawer and returns to the opener.
- Content via a `settings` slot; interim body explains the consolidation and links
  to History → Settings until **HS-30-08** migrates the full content.
- Wired with a small **vanilla** script (Alpine loads per-page and not on every
  route, so the shell must not depend on it). Bonus: `#settings` deep-links open
  the drawer on load.

### Decision — command palette deferred

The IA reserved a `⌘` slot. Decision: **defer the palette**; ship **no dead
control** (a non-functional ⌘ button is worse UX than none). The concept stays
reserved; revisit once the page surfaces stabilize. Recorded in current-phase-status.

## Tests

```bash
cd web && npm run build       # green, 8 pages, 4.21s
uv run pytest -q --ignore=tests/e2e/test_metal.py   # 2062 passed, 14 skipped
```

## Live evidence (screenshots) — `evidence/after-hs04/`

- `shell-desktop.png` (1440) — grouped nav (LIVE | Runtime active w/ underbar ·
  REVIEW | History Activity · CONFIGURE | Dictation Companion), brand, ⚙.
- `shell-drawer.png` — the Settings drawer open over a dimmed backdrop
  (`/_built/#settings`), header + close + interim content + accent CTA.
- `shell-mobile.png` (560) — brand + hamburger toggle + status + ⚙; content
  reflows to one column.

## Result

The shell is the consistent Signal frame for every route, with Settings now a
global destination (drawer) instead of History's 6th tab. **Next: HS-30-05** —
component library re-skin (uppercase eyebrows, primary glow, depth) + migrate the
89 shimmed `--wb-*` refs and **delete the tokens.css §3 shim**.
