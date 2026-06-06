# Phase 41 — Runtime Presence Indicators — Final Summary

- **Phase opened:** 2026-06-05
- **Phase closed:** 2026-06-05
- **Stories shipped:** 8 (HS-41-01 … HS-41-06, HS-41-08; HS-41-07 = this closeout)

## Goal — was it met?

Original goal:

> A user dictating into another app can't see the web dashboard. They should
> still **know what's happening** — listening / recording / transcribing /
> typing / done / error — from an ambient, on-desktop surface. Build that as an
> **opt-in** (`HOLDSPEAK_DESKTOP_PRESENCE=1`), per-platform **native** presence
> layer driven by one normalized activity contract, behind a pluggable renderer
> seam. Additive and off by default — flag unset ⇒ byte-identical, no GUI dep.

**Yes — and proven native on both OSes, on real hardware.**

- **macOS:** a focus-safe non-activating `NSPanel` hosting a `WKWebView` of the
  Signal `/presence` card (native rounding/shadow) + an `NSStatusItem` menu-bar
  glyph. Re-verified live in this closeout via `scripts/presence_macos_smoke.py`:
  `frontmost before: Terminal | after: Terminal | focus_stolen: False` —
  `SMOKE PASSED`. Capture: [`evidence/closeout_macos/macos_presence_hud.png`](./evidence/closeout_macos/macos_presence_hud.png)
  + the glyph strip.
- **Linux:** an in-place-updating libnotify notification (coalesced) + a
  StatusNotifierItem tray glyph (Tier 1, everywhere, focus-safe), **and** a
  floating GTK3 + WebKit2 overlay of the same `/presence` card (Tier 2, X11 /
  wlroots). Both **live-verified on `.43`** (Ubuntu 24.04/GNOME on X11) — the
  real notification banner ([`evidence/linux_presence_notification.png`](./evidence/linux_presence_notification.png))
  and the real overlay ([`evidence/linux_presence_overlay.png`](./evidence/linux_presence_overlay.png)).

## The safety invariant — held

**The presence surface never takes keyboard focus.** While it's visible,
keystrokes are being injected into the frontmost app, so any focus theft would
land them in the wrong window. Guaranteed at the platform level:

- macOS — `NSWindowStyleMaskNonactivatingPanel` (proven by the smoke run's
  `focus_stolen: False`).
- Linux — notifications + the tray can't be focused; the GTK overlay is an
  override-redirect, non-focus, click-through `POPUP`.

## Exit criteria — final state

- [x] **Real dogfood captured (state tracks; focus not stolen).** macOS smoke
      re-run live this closeout (`SMOKE PASSED`, focus not stolen). Linux Tier-1
      + Tier-2 live-verified on `.43` in HS-41-05/08.
- [x] **Full suite green; flag-off byte-identity re-asserted; no `_built/`
      tracked.** Presence + runtime-activity units: 37 passed. With the flag
      unset, `build_desktop_presence_host` returns `None` and the runtime is
      byte-identical (covered by `test_desktop_presence.py`). `git ls-files
      holdspeak/static/_built/` → **0**. Full suite: see HS-41-07 evidence.
- [x] **`final-summary.md` exists; status frozen; README → done; HANDOVER
      updated; PR opened/merged; codex PR #17 closed.** (this file; tracking docs
      updated in the closeout commit; PR + PR-#17 closure in the closeout.)

## What shipped (by story)

| Story | Outcome |
|---|---|
| HS-41-01 | The pure `runtime_activity` contract + `RuntimeActivityTracker` + transient `desktop_window_policy` (idle never renders), ported clean from the codex spike — no Tk, no deps. |
| HS-41-02 | Lifecycle → activity mapping + the `runtime_activity` websocket broadcast + a live Signal presence card on the dashboard (zero deps). |
| HS-41-03 | The desktop seam: `PresenceRenderer` Protocol + `DesktopPresenceHost` (show/linger/hide) + Wayland-aware `detect_presence_platform` (`overlay_capable`) + the flag-gated `build_desktop_presence_host`; the chromeless `/presence` HUD page + a framework-free WS driver (the native-webview content). |
| HS-41-04 | The **macOS** renderer — `CocoaPresenceRenderer` (non-activating `NSPanel` + `WKWebView` of `/presence` + `NSStatusItem` glyph; PyObjC `presence` extra), focus-safe, lazy child process, graceful fallback. (Also: toolchain fix — venv → uv-managed CPython 3.13.11.) |
| HS-41-05 | The **Linux** Tier-1 renderer — `FreedesktopPresenceRenderer` = in-place libnotify notification (coalesced) + StatusNotifierItem tray (PyGObject), focus-safe + portable across X11/Wayland + GNOME/KDE/XFCE; fully unit-tested + live on `.43`. |
| HS-41-08 | The **Linux** Tier-2 floating GTK-WebKit overlay (the macOS HUD's twin) — a non-focus, click-through GTK3 `POPUP` hosting a `WebKit2.WebView` of `/presence`, wired in when `overlay_capable`; live-captured on `.43`/X11. |
| HS-41-06 | User-facing docs — `docs/INTELLIGENT_TYPING_GUIDE.md` §11 "Desktop Presence" (enable flag + `.[presence]` extra + Linux typelibs; the state table; per-platform surfaces with real screenshots from both OSes; the Wayland caveat; the focus invariant) + cross-links; doc-guards green. |
| HS-41-07 | This closeout — live focus-safety re-verification, flag-off byte-identity, full suite, `final-summary.md`, README → done, HANDOVER, PR, codex PR #17 closed. |

## Tiering, as shipped

- **Tier 1 (everywhere, focus-safe):** tray glyph + in-place notification.
  The native path on mainstream Wayland (GNOME/KDE), where the compositor blocks
  arbitrary overlays.
- **Tier 2 (macOS · X11 · wlroots):** the rich floating webview HUD of the
  Signal `/presence` card. `build_desktop_presence_host()` probes the
  environment and selects the best available tier.

## Notes / carried items

- **codex PR #17** (the originating spike) is closed as superseded by this phase
  — its good bones (contract / Protocol / web card) were salvaged; its Tk
  renderer was deliberately rejected (couldn't meet the Signal bar, risked focus
  theft, reintroduced the Phase-32-retired desktop UI).
- Presence stays **opt-in**; making it on-by-default is explicitly out of scope.
- The optional native extras (`pyobjc` / `PyGObject`) are only pulled when the
  flag is on; the default test suite adds no GUI dependency.
