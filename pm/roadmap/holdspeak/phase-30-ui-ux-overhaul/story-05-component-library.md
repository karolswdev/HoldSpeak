# HS-30-05 — Component library re-skin

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
- **Depends on:** HS-30-03
- **Unblocks:** HS-30-06, HS-30-07, HS-30-08
- **Owner:** unassigned

## Problem

The token swap (HS-30-03) recolours the components, but their *form* is still
Workbench: hard 1px black hairlines, no radius, no depth, blue title strips,
diagonal-hatch disabled states. The shared component library has to be restyled
to the Signal grammar (depth, radius, glow, motion) so the page redesigns build
on correct primitives. The `/design/components` gallery is the contract.

## Scope

### In

- Restyle every component in `web/src/components/` to Signal:
  - `Button.astro` — variants/states on dark, primary with accent glow, disabled
    without the hatch artifact, motion on press/hover.
  - `Panel.astro` — surface card with real elevation + radius; replace the blue
    title-strip chrome with the Signal header treatment.
  - `Pill.astro` / `LocalPill.astro` — status/local pills retuned for dark.
  - `ListRow.astro`, `Toolbar.astro`, `EmptyState.astro`, `InlineMessage.astro`,
    `ConfirmDialog.astro`, `CommandPreview.astro`.
  - `AppMark.astro` / `HoldMark.astro` — brand marks in the new identity.
- Remove every lingering scoped-CSS reference to old Workbench tokens / VT323 /
  hairline idioms surfaced by HS-30-03's sweep.
- Update `/design/components.astro` to exercise all variants/states of every
  component as the visual contract.

### Out

- Page composition / layout (HS-30-06/07/08).
- New components — restyle the existing set only.

## Acceptance criteria

- [x] Every component in `web/src/components/` renders in Signal — eyebrow panel
      headers (no blue strip/pixel title), real depth + radius, primary glow.
- [x] `grep -roE -- '--wb-[a-z0-9-]*' web/src/components` returns **nothing** (was
      30 across 6 files). *Shim note: the tokens.css §3 shim stays until the page
      refs (59, in HS-30-06/07/08) are migrated — it is deleted with the last page
      (HS-30-08), not here.*
- [x] Disabled (flat grey, hatch retired), hover, focus, and active (accent-tint +
      inset accent marker) states defined for Button / ListRow / ConfirmDialog.
- [x] `/design/components` shows all variants/states — `evidence/after-hs05/components.png`.
- [x] `npm run build` green; backend sweep green (2062 passed, 14 skipped).

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual: `npm run dev`; screenshot the full `/design/components` gallery.
- Build: `npm run build` exit 0.

## Notes / open questions

- Focus rings must be visible on the dark canvas (the old orange-on-white ring is
  re-derived for dark in HS-30-02/03) — confirm here, finalize in HS-30-09.
- Keep Astro scoping; no global class leakage between components.
