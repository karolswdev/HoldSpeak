# HS-30-05 Evidence — Component library re-skin

**Date:** 2026-06-02.
**Story:** [story-05-component-library.md](./story-05-component-library.md).

## Implementation Evidence

Every component in `web/src/components/` is restyled to Signal and the **30
direct `--wb-*` refs (across 6 files) are migrated to canonical tokens** — `grep`
on the components dir now returns zero.

- **Button** — primary carries `--glow-accent`; the Workbench diagonal-hatch
  disabled state is retired for a flat grey (design-language §7); danger fixed to
  white-on-`--danger-fill` (AA); radius → `--radius-md`.
- **Panel** — raised `--surface-1` card with `--radius-lg` + `--elev-1`; the blue
  title-strip becomes a quiet `--surface-2` header whose title is an
  **uppercase-tracked eyebrow** (the technical cue that replaces the pixel strip).
- **Pill** — `--wb-gray*`/`--wb-blue*` → `--text-muted`/`--surface-2`/`--border`;
  local tone → info-cyan.
- **ListRow** — subtle divider; hover → `--surface-hover`; selected → accent-tint
  fill **+ an inset accent left-marker** (dual-encoded, not colour-only).
- **EmptyState** — accent glyph in a raised rounded tile.
- **CommandPreview** — recessed `--bg` code well, `--radius-md`, info-cyan neutral
  tone edge.
- **ConfirmDialog** — `--surface-2` dialog, `--radius-lg`, `--elev-3`; header →
  `--surface-3` with a real title; scope pill → info tone.

### Shim status

The component refs are gone, but the **tokens.css §3 `--wb-*` shim stays**: pages
still hold **59** refs (history/activity/dictation/index), migrated in
HS-30-06/07/08. The shim is deleted with the **last page (HS-30-08)** — deleting
it now would break the pages. (Corrects the HS-30-04 note that put deletion here.)

## Tests

```bash
grep -roE -- '--wb-[a-z0-9-]*' web/src/components | wc -l   # 0  (was 30)
cd web && npm run build                                     # green, 8 pages
uv run pytest -q --ignore=tests/e2e/test_metal.py           # 2062 passed, 14 skipped
```

## Live evidence

`evidence/after-hs05/components.png` — the `/design/components` gallery: eyebrow
panel headers, glowing primary button, flat-grey disabled (no hatch), status
pills, ListRow selected marker, EmptyState accent tile — one cohesive dark system.

## Result

The shared component vocabulary is fully Signal. **Next: HS-30-06** — redesign the
runtime dashboard (`index.astro`) to the IA spec (meeting-state hero, dominant
transcript, grouped intel rail), the first per-page redesign + the start of
migrating the page `--wb-*` refs.
