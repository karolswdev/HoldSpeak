# Evidence — HS-44-03 — History polish

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-44-daily-surface-polish`

## What shipped
A behavior-preserving premium pass on **history (`/history`)** — the third
daily-driver surface lifted to the Phase-43 wizard's bar. History wore the older
flat "Workbench" treatment (square corners, hard borders, notebook tabs); it now
matches the dashboard and cockpit. **CSS-only** — every class name and the full
Alpine DOM contract (`historyApp()`, the tab system, the artifact/risk-table/
incident-timeline selectors the spoken-e2e reads) is untouched.

- **Ambient accent glow** (`.shell::before` radial gradient) — the same
  top-of-page glow as the dashboard home (HS-44-01) and the cockpit (HS-44-02).
- **Elevated hero** (`web/src/pages/history.astro`) — a raised, rounded
  (`--radius-lg`) surface with `--elev-1` depth and a top-left accent-tint wash,
  a **mono accent eyebrow**, and a **bold display headline** (clamp-scaled,
  `font-weight: 700`, tight tracking). Retired the flat square panel +
  weight-400 title.
- **Premium pill tab bar** — the `.tab-row` is now a contained, elevated pill
  bar (surface tint + border + `--elev-1` + blur); the **active** tab is a punchy
  solid accent. Retired the square notebook tabs.
- **Rounded, elevated section + metric cards.**
- **Depth + motion** — archive rows (meeting / action / speaker cards) gain a
  rounded surface + an accent border + a hover lift (`translateY(-2px)` + accent
  shadow); the read-only transcript `.segment` rows stay calm. Reduced-motion-safe.

## Behavior preservation
No markup changed — the edits are confined to the `<style>` block, so every
class name, `x-data`/`x-show`/`@click` binding, and the spoken-e2e artifact
selectors are byte-identical. Asserted by the new test.

## Verification
- **Live (Playwright):** the archive renders the glowing rounded hero, the
  solid-accent pill tab bar, and the elevated section. Screenshot:
  [`history_archive.png`](./evidence/history_archive.png).
- `tests/integration/test_web_history_archive.py` — the glow + elevated hero +
  pill tabs, reduced-motion-safe card motion, and the preserved DOM contract
  (the `historyApp` factory, the five tabs, and the card/artifact/table class
  names).
- Full suite: **2328 passed, 16 skipped**
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Acceptance criteria
- [x] History is visibly elevated to the wizard's bar (glow + rounded elevated
      hero + premium pill tabs + card depth/motion); behavior unchanged
      (CSS-only, DOM contract preserved); reduced-motion + a11y; suite green;
      0 `_built/`.
