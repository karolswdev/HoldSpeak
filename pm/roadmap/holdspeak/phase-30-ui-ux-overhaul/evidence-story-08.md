# HS-30-08 Evidence — History + Activity + Companion + shim deletion

**Date:** 2026-06-02.
**Story:** [story-08-secondary-pages-redesign.md](./story-08-secondary-pages-redesign.md).

## Implementation Evidence

The last three routes are migrated to Signal and the **tokens.css Workbench compat
shim is deleted** — `--wb-*` is now **zero across all of `web/src`**, completing
the phase's token migration.

- **Ref migration (behaviour-preserving).** history (20), activity (15), companion
  (2), and the design gallery (1) still referenced `--wb-*` via the shim. Each ref
  was inlined to the shim's exact Signal target (`--wb-black`→`--border`,
  `--wb-white`→`--text`, `--wb-blue`→`--surface-2`, grays→surfaces, `--wb-*-tint`→
  status/accent tints) — a pure refactor that renders identically, then the shim
  (`tokens.css` §3) was removed.
- **Signal polish.** Activity's local `.panel`/`.panel-header` became a raised card
  with an uppercase **eyebrow** header (matching the rest). History + Companion
  already read as consistent Signal (eyebrow page headers, metric/summary cards,
  dark panels) once the refs resolved to canonical tokens.
- **No behaviour touched.** All three are driven by their own JS (`historyApp()`,
  the activity IIFE, `CompanionApp()`); the change is CSS only — no `x-*` /
  `data-*` / element-`id` hook was modified.

### Shim deleted

```
tokens.css §3 (the --wb-* compat shim)  -> removed
grep -rnoE -- '--wb-[a-z0-9-]*' web/src  -> 0   (was ~108 at HS-30-03)
```

### Deferred (flagged, not dropped)

History keeps its **Settings** tab. The IA's full extraction of Settings *content*
into the shell drawer is a larger `historyApp()` + settings-endpoint refactor; the
drawer (HS-30-04) already exists and links into History → Settings, so settings are
globally reachable. Full extraction is handed to a follow-up (recorded in
`final-summary.md` at HS-30-09) rather than risking it on this restyle chunk.

## Tests

```bash
grep -rnoE -- '--wb-[a-z0-9-]*' web/src             # 0  (shim gone, all pages migrated)
cd web && npm run build                             # green, 8 pages
uv run pytest -q --ignore=tests/e2e/test_metal.py   # 2062 passed, 14 skipped
```

## Live evidence — `evidence/after-hs08/`

- `history.png` — eyebrow "MEETING ARCHIVE" header, 4 metric cards, the tab row,
  orange Search, dark cards.
- `activity.png` — Signal panels with eyebrow headers across the controls/sources/
  rules/records columns.
- `companion.png` — eyebrow "AI PI COMPANION" header, summary cards with mono
  values, consistent panels.

## Result

The entire product is now Signal end-to-end, with zero Workbench tokens. **Next:
HS-30-09** — accessibility (AA contrast verify), motion / reduced-motion, a
cross-route polish pass, and the phase exit (`final-summary.md`).
