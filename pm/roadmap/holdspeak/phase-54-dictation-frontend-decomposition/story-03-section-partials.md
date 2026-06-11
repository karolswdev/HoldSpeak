# HS-54-03 — Section partials (carve dictation.astro)

- **Project:** holdspeak
- **Phase:** 54
- **Status:** backlog
- **Depends on:** HS-54-02
- **Unblocks:** HS-54-04, HS-54-05, HS-54-06
- **Owner:** unassigned

## Problem
`web/src/pages/dictation.astro` is 3,134 lines: ~814 lines of markup hosting nine tab
panels plus a single ~2,318-line `<style>` block sectioned only by comments. Finding
the markup or styles for one tab means scrolling a 3k-line file; every new section
grows it further.

## Scope
- **In:**
  - Carve the page into Astro components under `web/src/components/dictation/`: one
    partial per tab panel (Readiness, Blocks, Runtime, Memory, Journal, Dry-run,
    Project Facts, Project Context + guided-setup modal, Agent Hooks) plus the cockpit
    hero, the discovery-nudge card, the activity pre-briefing shell, and the meta
    banners. The page file becomes a thin composition (~≤300 lines) preserving exact
    DOM order.
  - **Styles ride with their partial.** Each partial carries the style rules for its
    own markup; rules that target **JS-injected DOM** (activity nudge cards, journal
    entries, learning digest, readiness cards, block list, trace stages…) move into
    explicit `<style is:global>` blocks colocated with the partial that hosts the
    container, per the established rule.
  - The hidden `CommandPreview` + script injection block stays functionally identical.
  - **Screenshot-verify every tab before/after** (`scripts/screenshot_*.py` pattern);
    commit the evidence pairs.
- **Out:** any visual change (pixel-faithful is the bar); renaming ids/classes; JS
  changes beyond import-path touch-ups; shared cross-page components.

## Acceptance criteria
- [ ] `dictation.astro` is a thin composition (~≤300 lines); each tab's markup +
      styles live in its partial under `web/src/components/dictation/`.
- [ ] Styles targeting JS-injected DOM are explicitly `is:global` and verifiably
      apply (screenshot, not bundle-grep).
- [ ] Before/after screenshots per tab committed and visually identical.
- [ ] All page-content tests pass **unmodified**; full suite green; `npm run build`
      clean; 0 `_built/` tracked.

## Test plan
- `uv run pytest -q tests/integration -k "dictation or cockpit"`, then the full suite
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).
- Screenshot sweep across all nine tabs (+ nudge states) before and after the carve;
  visual diff.

## Notes / open questions
- Astro scoping changes class-attribution when markup moves between files — this is
  the story where the scoped-CSS gotcha bites hardest. When in doubt whether a rule's
  target is static or JS-rendered, check who creates the node, not where the class is
  written.
