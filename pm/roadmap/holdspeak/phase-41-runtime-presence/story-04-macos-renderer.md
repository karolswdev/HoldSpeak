# HS-41-04 — macOS renderer (NSStatusItem + NSPanel webview)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** backlog
- **Depends on:** HS-41-03
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The premium macOS presence: ambient + rich, native, focus-safe.

## Scope

- In:
  - `CocoaPresenceRenderer` (PyObjC, optional extra — lazy import behind the flag):
    - **Tier 1:** an `NSStatusItem` menu-bar glyph — a custom template/colored
      image in the accent that reflects state (pulses while active).
    - **Tier 2:** a non-activating `NSPanel`
      (`NSWindowStyleMaskNonactivatingPanel`, `.floating` level, `hasShadow`,
      layer `cornerRadius`, `ignoresMouseEvents`) hosting a **`WKWebView`** loaded
      at the local `/presence` URL — the Signal card, live over the websocket.
    - Show/hide per the window policy; spring fade via `NSAnimationContext`.
  - Runs AppKit on the right thread/runloop; graceful fallback to Null if PyObjC
    is unavailable.
  - `pyobjc` added as an optional extra in `pyproject.toml`.
  - Verification script + **screenshot evidence** (HUD + glyph, real macOS).
- Out:
  - Linux (HS-41-05).

## Acceptance criteria

- [ ] With the flag on (macOS), the menu-bar glyph + the floating HUD render and
      track state; **focus is never stolen** (proven — keystrokes still land in
      the prior frontmost app).
- [ ] PyObjC absent ⇒ graceful Null fallback; default suite unaffected.
- [ ] Rich Signal (it *is* the web card); screenshot captured.

## Notes

- The focus test is the headline: assert/observe that activating the HUD does
  not change the frontmost app.
