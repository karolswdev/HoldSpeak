# HS-111-09 - Sprite and icon quality

- **Project:** holdspeak
- **Phase:** 111
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

The pixel-art icon family is the one element that already speaks
Workbench — but some dock sprites shipped rough, and the window type
icons and overview/reset glyphs lag the standard. The bar: **every
sprite on the desk earns its place — regenerated where bad, judged on
the real desk at real size, one family voice.** Art is tested on the
desk, not approved in a generator preview.

## Method (phase canon)

1. **Audit.** An agent screenshots the dock, window type icons, and
   overview/reset glyphs on the real desk and files which sprites
   read badly at rendered size.
2. **Rethink.** Regenerate the bad ones (Pixellab pipeline) in the
   established family style; iterate on the desk, not in previews.
3. **Implement** — wire the regenerated assets in `web/src`.
4. **Prove** with live desk screenshots before/after at both
   viewports.

## Test plan

- Every dock sprite reads cleanly at its rendered size on the real
  desk (no mud, no mixed resolution).
- Window type icons and overview/reset glyphs match the family voice.
- Before/after screenshot pairs captured on the live hub.
