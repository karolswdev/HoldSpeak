# Phase 41 — Runtime Presence Indicators

**Status:** IN PROGRESS (6/8 stories). Opened 2026-06-05 (grew 7→8 on user ask:
un-defer the Linux floating overlay). Direction chosen by the
user: **know what the copilot is doing on the desktop** while dictating —
without the web dashboard being visible — via a rich, branded, native-feeling
presence indicator on **both macOS and Linux**.

**Last updated:** 2026-06-05 (**HS-41-08 done** — the Linux **floating GTK-WebKit
overlay** (the macOS HUD's twin), live-captured on `.43`/X11: the same Signal
card in a GTK3 POPUP, served from the Mac over an SSH reverse tunnel. Suite
2261/16. HS-41-05 done — the Linux renderer:
`FreedesktopPresenceRenderer` = an in-place-updating libnotify notification
(coalesced) + a StatusNotifierItem tray glyph, focus-safe + portable across
X11/Wayland + GNOME/KDE/XFCE; logic fully unit-tested with fakes **and
live-verified on real Ubuntu 24.04/GNOME (`.43`)** — the actual renderer showed a
real notification banner. The Tier-2 floating GTK-WebKit overlay is a deferred
follow-up (`.43` is X11 + has WebKit2, so it's buildable there). Suite 2259/16.
HS-41-01–04 also done.).

## Goal

A user dictating into another app can't see the web dashboard. They should still
**know what's happening** — listening / recording / transcribing / typing /
done / error — from an ambient, on-desktop surface. This phase builds that as an
**opt-in** (`HOLDSPEAK_DESKTOP_PRESENCE=1`), per-platform native presence layer
driven by one normalized activity contract, behind a pluggable renderer seam.

It is **additive and off by default** — with the flag unset, the runtime is
byte-identical and adds no GUI dependency surface.

## Origin & decisions

This grew out of a parallel spike (codex PR #17, "[codex] HS-40 runtime presence
indicators"). That PR's **bones are good and salvaged** — the normalized
`runtime_activity` contract, the lifecycle→state mapping, the `PresenceRenderer`
Protocol seam, and a Signal-styled **web presence card**. Its **Tk renderer is
rejected** — a borderless Tk window can't match the Signal bar (no rounded
corners / shadow / vibrancy), risks **stealing keyboard focus** from the
dictation target, and reintroduces the native-desktop-UI surface Phase 32
deliberately retired. PR #17 stays open as reference and is closed when this
phase lands.

**Locked decisions (user, 2026-06-05):**

- **HUD substrate = webview of the Signal card.** The rich floating HUD is a
  **frameless, always-on-top webview** pointed at a tiny local `/presence`
  route, driven live by the existing `runtime_activity` **websocket broadcast**.
  One design (the Signal card), zero redesign, animations for free. Native code
  shrinks to: the window chrome (non-activating `NSPanel` / GTK overlay), the
  status-bar/tray glyph, and the show/hide policy.
- **Go native on both OSes now.** macOS (`pyobjc`) + Linux (`PyGObject`/D-Bus)
  as **optional extras** — only pulled/active when the flag is on; the core
  stays slim.

**The focus invariant (non-negotiable):** the presence surface must **never take
keyboard focus** — while it's visible, keystrokes are being injected into the
frontmost app. macOS `NSWindowStyleMaskNonactivatingPanel` and freedesktop
notifications/tray guarantee this at the platform level (Tk did not).

**The Wayland reality:** on mainstream Wayland (GNOME/KDE) arbitrary always-on-top
overlays are blocked by the compositor (the same restriction that forced the
Phase-39 model-assisted target detection). There, the native path is the
**branded tray glyph + replace-in-place notification** (Tier 1); the floating
webview HUD (Tier 2) is available on macOS, X11, and wlroots compositors.

## Tiering

- **Tier 1 — everywhere, zero-overlay, focus-safe, branded:** an animated
  status-bar/tray glyph (custom pixels in the accent) + an in-place-updating
  notification with a per-state icon.
- **Tier 2 — where the platform allows (macOS · X11 · wlroots):** the rich
  **floating webview HUD** of the Signal presence card.

`build_desktop_presence_host()` probes the environment and selects the best
available tier; everything is gated by `HOLDSPEAK_DESKTOP_PRESENCE=1`.

## Scope

### In

- The normalized **runtime-activity contract** + lifecycle→state mapping +
  `runtime_activity` websocket broadcast (HS-41-01).
- The **web presence card** — the always-available, zero-dep surface (HS-41-02).
- The **`PresenceRenderer` Protocol** + Null renderer + env-probing host
  selection + the opt-in flag + a `/presence` route for the HUD webview (HS-41-03).
- The **macOS** renderer — `NSStatusItem` glyph + non-activating `NSPanel`
  hosting the `/presence` webview (HS-41-04).
- The **Linux** renderer — D-Bus notification (replace-in-place) +
  StatusNotifierItem tray; GTK-WebKit overlay where allowed (HS-41-05).
- **Documentation** (HS-41-06) + **closeout** (HS-41-07).

### Out

- Making presence on by default (stays opt-in).
- A rich floating overlay on Wayland-GNOME/KDE (platform-blocked; Tier 1 there).
- Replacing the web dashboard (this is an *ambient* companion to it).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-41-01 | Runtime activity contract + state mapping | done | [story-01-runtime-activity-contract.md](./story-01-runtime-activity-contract.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-41-02 | Web presence card (zero-dep surface) | done | [story-02-web-presence-card.md](./story-02-web-presence-card.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-41-03 | Renderer Protocol + host selection + `/presence` route | done | [story-03-renderer-seam.md](./story-03-renderer-seam.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-41-04 | macOS renderer (NSStatusItem + NSPanel webview) | done | [story-04-macos-renderer.md](./story-04-macos-renderer.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-41-05 | Linux renderer (notification + tray) | done | [story-05-linux-renderer.md](./story-05-linux-renderer.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-41-08 | Linux GTK-WebKit floating overlay | done | [story-08-linux-gtk-overlay.md](./story-08-linux-gtk-overlay.md) | [evidence-story-08.md](./evidence-story-08.md) |
| HS-41-06 | Documentation | backlog | [story-06-documentation.md](./story-06-documentation.md) | — |
| HS-41-07 | Closeout | backlog | [story-07-closeout.md](./story-07-closeout.md) | — |

## Where we are

**HS-41-01 → HS-41-05 + HS-41-08 done (2026-06-05).** Branched `phase-41-runtime-presence`
off `main` (post Phase-40 merge). HS-41-01 ported the pure `runtime_activity`
contract; HS-41-02 wired the full lifecycle into it + the WS broadcast + the
dashboard presence card (zero deps). **HS-41-03** built the desktop seam:
`PresenceRenderer` Protocol + `DesktopPresenceHost` (transient show/linger/hide)
+ `build_presence_window_view` (secret-redacted, renderer-ready) +
**`detect_presence_platform`** (Wayland-aware — `overlay_capable` False on
GNOME/KDE-Wayland, True on macOS/X11/wlroots) + the flag-gated
`build_desktop_presence_host` (None until a native renderer registers), re-wired
into `web_runtime`. The **`/presence`** HUD page (chromeless, transparent,
token-styled) + `presence-app.js` (framework-free WS driver) render the Signal
card live — the exact content the native webview hosts. **HS-41-04** built the
**macOS** renderer: `CocoaPresenceRenderer` (PyObjC, the optional `presence`
extra) drives a **non-activating `NSPanel`** hosting a **`WKWebView`** of
`/presence` (native rounding/shadow — the Signal card) + an `NSStatusItem`
glyph, in a lazy-started child process. **Focus-safe** (the smoke run proved the
frontmost app is unchanged when the HUD shows) + graceful fallback when
WebKit/GUI is absent; live native screenshots captured. (Also: fixed the broken
Homebrew python@3.13 bottle by switching the venv to uv-managed CPython 3.13.11
— `uv run` works again.) **HS-41-05** built the **Linux** renderer:
`FreedesktopPresenceRenderer` = an in-place-updating **libnotify notification**
(coalesced on state change) + a **StatusNotifierItem tray glyph** (PyGObject,
lazy), focus-safe and portable across X11/Wayland + GNOME/KDE/XFCE. Logic fully
unit-tested with fake seams; graceful fallback verified
(`freedesktop_presence_available()` False on macOS) **and live-verified on
`.43`/GNOME** (a real notification banner). **HS-41-08** un-deferred the Tier-2
floating overlay (user ask): `desktop_presence_gtk.py` — a GTK3 POPUP
(override-redirect/keep-above/non-focus/transparent/click-through) hosting a
`WebKit2.WebView` of `/presence`, fork-child-driven, wired into the freedesktop
renderer when `overlay_capable`. **Live-captured on `.43`/X11** — the same Signal
card as the macOS HUD, served from the Mac over an SSH reverse tunnel. Both
renderers + the overlay are now proven on real hardware. Suite 2261/16. Next:
**HS-41-06** (documentation) → **HS-41-07** (closeout).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Presence window steals keyboard focus from the dictation target | High if naive | macOS non-activating `NSPanel`; notifications/tray never take focus; an explicit focus-safety test/dogfood | Injected text lands in the wrong app |
| New native deps bloat the core / break headless/CI | Medium | `pyobjc`/`PyGObject` are **optional extras**, imported lazily behind the flag; Null renderer + graceful fallback; default suite adds no GUI dep | CI/import breaks with the flag unset |
| Wayland-GNOME/KDE can't show the floating HUD | Certain (platform) | Documented; Tier-1 tray+notification is the native path there | A floating overlay is promised but blocked |
| The codex spike's stale base conflicts on port | Medium | Port files selectively onto current `main`, don't rebase the branch | Merge noise in `web_runtime.py` / roadmap README |

## Decisions deferred

- **Tray on GNOME needs the AppIndicator extension** — trigger HS-41-05 —
  default: document the wart + degrade to notification-only when no tray host.
- **Whether the HUD webview is the full dashboard or a dedicated `/presence`
  page** — trigger HS-41-03 — default: a dedicated minimal `/presence` route
  (transparent bg, HUD-sized, just the card).
