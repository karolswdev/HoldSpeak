# Phase 41 — Runtime Presence Indicators

**Status:** IN PROGRESS (1/7 stories). Opened 2026-06-05. Direction chosen by the
user: **know what the copilot is doing on the desktop** while dictating —
without the web dashboard being visible — via a rich, branded, native-feeling
presence indicator on **both macOS and Linux**.

**Last updated:** 2026-06-05 (**HS-41-01 done** — the platform-agnostic
`runtime_activity` contract + tracker, salvaged from the codex spike and ported
clean; suite green).

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
| HS-41-02 | Web presence card (zero-dep surface) | backlog | [story-02-web-presence-card.md](./story-02-web-presence-card.md) | — |
| HS-41-03 | Renderer Protocol + host selection + `/presence` route | backlog | [story-03-renderer-seam.md](./story-03-renderer-seam.md) | — |
| HS-41-04 | macOS renderer (NSStatusItem + NSPanel webview) | backlog | [story-04-macos-renderer.md](./story-04-macos-renderer.md) | — |
| HS-41-05 | Linux renderer (notification + tray + overlay) | backlog | [story-05-linux-renderer.md](./story-05-linux-renderer.md) | — |
| HS-41-06 | Documentation | backlog | [story-06-documentation.md](./story-06-documentation.md) | — |
| HS-41-07 | Closeout | backlog | [story-07-closeout.md](./story-07-closeout.md) | — |

## Where we are

**HS-41-01 done (2026-06-05).** Branched `phase-41-runtime-presence` off `main`
(post Phase-40 merge, suite 2221/16). Ported the pure `runtime_activity`
contract from the codex spike (no Tk, no deps) + its tests. The
event-mapping wiring into `web_runtime` + the websocket broadcast land with
HS-41-02 (so the web card has data). Next: **HS-41-02** (the web presence card —
the first visible win, zero new deps).

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
