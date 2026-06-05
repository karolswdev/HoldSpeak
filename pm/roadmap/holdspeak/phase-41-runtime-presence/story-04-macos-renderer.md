# HS-41-04 — macOS renderer (NSStatusItem + NSPanel webview)

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done (2026-06-05)
- **Depends on:** HS-41-03
- **Unblocks:** none
- **Owner:** unassigned
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

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

- [x] With the flag on (macOS), the menu-bar glyph + the floating HUD render and
      track state; **focus is never stolen** (proven — frontmost unchanged
      Terminal→Terminal).
- [x] PyObjC absent ⇒ graceful fallback (Cocoa not selected); default suite unaffected.
- [x] Rich Signal (it *is* the web card, in a native shadowed/rounded panel);
      screenshot captured.

## Outcome

`CocoaPresenceRenderer` (PyObjC, optional `presence` extra) renders a
**non-activating `NSPanel`** hosting a **`WKWebView`** of `/presence` (native
rounding + shadow, the Signal card) + a color-keyed `NSStatusItem` glyph, driven
in a child process (lazy-started on first show). **Focus-safe** — the smoke run
proved the frontmost app is unchanged when the HUD appears. Graceful fallback to
the web card when WebKit/GUI is absent. Live screenshots in `evidence/`. Suite
2251/16. See [evidence-story-04.md](./evidence-story-04.md).

## Notes

- The focus test is the headline: assert/observe that activating the HUD does
  not change the frontmost app.
