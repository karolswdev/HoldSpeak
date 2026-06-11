# Evidence — HS-54-05: Docs — the frontend architecture pattern

**Date:** 2026-06-11
**Branch:** `phase-54-dictation-frontend`

## 1. The doc

`docs/internal/ARCHITECTURE_WEB_FRONTEND.md` records the pattern as it
actually shipped (verified against the tree, not the plan):

- **The shape:** thin page → section partials + markup-less shared-style
  components → thin script entry → single-concern behavior modules, with the
  density-guard budgets (page ≤300, entry ≤50, components/modules ≤600) and
  the carve-don't-bump rule.
- **The module seam decision (HS-54-01):** what the `?raw` + `new Function()`
  loader was (the Phase-10 migration shim), what replaced it, why client
  chunks ship un-minified (the Astro 6 `configEnvironment` override + the
  rationale), and that other pages keep their shims until carved.
- **The behavior-module idiom (HS-54-02):** the section-loader registry that
  keeps the module graph acyclic; one shared-state module; where shared
  helpers live.
- **The style rules (HS-54-03):** the attribute-scoping trap (with the
  latent-bug finding), the who-creates-the-node test for `is:global`, and
  the import-order rule that preserves the cascade.
- **A concrete six-step "add a section to the dictation cockpit"
  walkthrough**, written to be followable without reading this phase's
  history.
- **Follow-ups:** `history.astro` / `index.astro` named as the next
  candidates, with the warning to probe their JS-rendered DOM for the same
  latent scoping bug.

Linked from `CONTRIBUTING.md`'s development section (next to the existing
"rebuild the bundle" note, where a web contributor already looks).

## 2. Guards + suite (actually run, actually read)

The Phase-51 roadmap-vocab guard is scoped to user-facing docs (README +
non-recursive `docs/*.md`); this internal doc is intentionally outside it and
uses roadmap vocabulary freely. No user-facing doc was modified
(CONTRIBUTING.md is contributor-facing and outside the guard's scope; its
addition is product-tense anyway).

```
$ uv run pytest -q tests/unit -k "doc or drift or density"
74 passed, 1950 deselected in 1.52s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2545 passed, 17 skipped in 76.25s (0:01:16)
```
