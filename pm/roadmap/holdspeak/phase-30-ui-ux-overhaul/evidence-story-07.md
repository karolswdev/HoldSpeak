# HS-30-07 Evidence — Dictation redesign

**Date:** 2026-06-02.
**Story:** [story-07-dictation-redesign.md](./story-07-dictation-redesign.md).

## Implementation Evidence

`web/src/pages/dictation.astro` is redesigned to the IA spec on Signal, with no
change to its (vanilla-JS) behaviour.

- **Local Workbench CSS → Signal.** Migrated the page's `.panel`/`.panel-header`/
  `.meta-banner`/`.hook-card`/`.block-card`/`.agent-context-banner` styles: panels
  are raised `--surface-1` cards (`--radius-lg`, `--elev-1`) with **uppercase
  eyebrow** headers; banners/cards get borders + radius from the Signal tokens;
  block cards hover on `--surface-hover`. The page's **13 `--wb-*` refs → 0**.
- **7 tabs → two tiers (IA §4b).** A `.tab-tier-sep` divider splits the section
  tablist into **Setup** (Readiness, Blocks, Project KB, Project Context, Agent
  Hooks) and **Runtime & test** (Runtime, Dry-run) — progressive disclosure
  without changing the tab set. The active section/scope tabs use the accent-tint
  pill state.
- The form fields inherit `--field-bg`/`--field-border` (now dark) + the global
  accent focus ring; the dry-run trace + block editor read on dark.

Behaviour is preserved **by construction**: dictation is driven by
`dictation-app.js` via `data-section`/element-`id` hooks — none were touched. The
change is CSS migration + one non-interactive separator span.

## Tests

```bash
grep -cE -- '--wb-' web/src/pages/dictation.astro   # 0  (was 13)
cd web && npm run build                             # green, 8 pages
uv run pytest -q --ignore=tests/e2e/test_metal.py   # 2062 passed, 14 skipped
```

## Live evidence

`evidence/after-hs07/dictation.png` (1440) — the Blocks tab: the two-tier tablist
(separator before Runtime), Signal panels with eyebrow headers ("BLOCKS", "SELECT
A BLOCK TO EDIT"), the project-root row with the orange Apply, dark forms. Compare
`evidence/before/before-dictation.png`.

## Result

Dictation is Signal + progressively disclosed. **Next: HS-30-08** — History +
Activity + Companion redesign, which migrates the last page `--wb-*` refs and
**deletes the tokens.css §3 shim**.
