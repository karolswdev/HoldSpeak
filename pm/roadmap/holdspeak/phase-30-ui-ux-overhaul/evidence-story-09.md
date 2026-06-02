# HS-30-09 Evidence — Accessibility + motion + polish + phase exit

**Date:** 2026-06-02.
**Story:** [story-09-a11y-motion-exit.md](./story-09-a11y-motion-exit.md).

## Accessibility — contrast (verified, not eyeballed)

`evidence/a11y-contrast.py` computes WCAG 2.1 ratios for every Signal pairing
against the real token hex values. **All functional pairings pass AA or AAA:**

| pairing | ratio | verdict |
|---|---|---|
| `--text` on `--bg` | 17.25 | AAA |
| `--text-muted` on `--bg` | 7.47 | AAA |
| `--text-faint` on `--bg` (meta) | 4.69 | AA |
| `--accent` on `--bg` | 6.76 | AA |
| `--ok` / `--warn` / `--info` on `--bg` | 9.96 / 11.47 / 9.93 | AAA |
| `--danger` on `--bg` | 6.92 | AA |
| `--text-muted` on `--surface-2` | 6.42 | AA |
| dark ink on `--accent` (primary btn) | 6.76 | AA |
| white on `--danger-fill` (danger btn) | 4.83 | AA |
| ~~white on `--accent`~~ | 2.84 | **FAIL → forbidden, never shipped** |

The only failing combination is the one the design language explicitly forbids
(white-on-orange); the primary button uses dark ink (6.76). `--text-faint` is
reserved for non-essential meta/hints (passes the 3:1 large/non-text bar; ~4.0–4.7
in practice). No token needed changing.

## Motion / reduced-motion

`tokens.css` carries a `@media (prefers-reduced-motion: reduce)` block that forces
all `animation-duration` / `transition-duration` to `0ms !important` and pins
`animation-iteration-count: 1`. This covers the brand pulse (`hs-pulse`), the
button spinner, the dry-run caret, and every transition — reduced-motion is
honoured product-wide from one place.

## Focus + keyboard

The accent focus ring is defined globally (`:focus-visible` in `global.css`) and
re-stated per interactive component (Button, Pill, ListRow, TopNav links, the
Settings ⚙/close, nav toggle) as a 2px accent outline on the dark canvas — visible
on every surface. The shell skip-link, the Settings drawer (Escape + focus
move/return), and the nav are keyboard-operable.

## Cross-route consistency

The five routes share one vocabulary after HS-30-04…08: eyebrow page + panel
headers, raised `--surface-1` cards with `--elev-1`/`--radius-lg`, the accent
reserved for primary/live/focus, mono for data. Verified across
`evidence/after-hs0{4,5,6,7,8}/`. No route is off-system.

## Exit gate

```bash
python3 evidence/a11y-contrast.py        # ALL PASS
cd web && npm run build                  # green, 8 pages
uv run pytest -q --ignore=tests/e2e/test_metal.py   # 2062 passed, 14 skipped
grep -rnoE -- '--wb-[a-z0-9-]*' web/src  # 0  (zero Workbench tokens)
```

## Result

Phase 30 is complete: the Amiga Workbench UI is fully retired for **"Signal"**, a
bold dark identity, AA-clean and consistent across all five routes. `final-summary.md`
written; this phase is closed. One follow-up is handed off (History → Settings
content extraction into the shell drawer).
