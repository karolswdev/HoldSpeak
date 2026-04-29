# HS-10-10 - `CommandPreview` component

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-02, HS-10-03
- **Unblocks:** HS-10-09
- **Owner:** karol

## Problem

The product surfaces shell commands and command-like traces in three
places — gh enrichment preview, jira enrichment preview, and the
dictation dry-run trace. Each currently renders these in a different
ad-hoc block. The handoff explicitly calls out "command previews need
a standardized monospaced, copyable, inspectable style."

## Scope

- **In:**
  - `web/src/components/CommandPreview.astro` with:
    - Monospaced rendering using the mono token from HS-10-02.
    - Stable wrap behavior — long arguments wrap at logical boundaries
      and never produce horizontal scroll inside a panel.
    - Copy-to-clipboard button with a transient "copied" pill.
    - Optional `caption` slot above the block (e.g. "this command will
      run if you click Run").
    - Optional `meta` slot below for status pills (success/failed/
      skipped) and timing.
    - `tone=neutral|warn|danger` for plan vs run-failed vs dangerous-
      preview.
  - Adoption in `/activity` connector previews (replacing whatever
    HS-10-07 placed there as a stand-in).
  - Adoption in `/dictation` dry-run trace (HS-10-09 depends on this
    component).
- **Out:**
  - Syntax highlighting beyond monospaced typography.
  - Editable command previews — these are read-only by design.

## Acceptance Criteria

- [x] `CommandPreview` exists, is rendered in the components gallery
  in every documented state, and consumes only tokens.
- [x] Copy-to-clipboard works in Chrome and Safari; the success pill
  auto-dismisses after a short delay.
- [x] Long commands (≥200 chars, including a long URL) wrap without
  horizontal scroll at 768px.
- [x] The component is used in every place a command or command-trace
  is shown in the product.

## Test Plan

- Manual gallery walk in two viewports.
- Manual copy-clipboard test in Chrome and Safari.
- Manual integration check on `/activity` and `/dictation` after
  HS-10-07 / HS-10-09 land.

## Notes

This is the smallest story in the phase but probably the highest
satisfaction-per-line-of-code — these blocks appear constantly during
dogfooding, and the current ad-hoc renderings undermine confidence in
the very behaviors (preview-before-run) the product is built around.
