# Evidence — HS-41-04 — macOS renderer (NSStatusItem + NSPanel webview)

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-41-runtime-presence`
- **Owner:** unassigned

## What shipped

The premium macOS presence surface — the "webview of the Signal card" delivered
natively, and **focus-safe**.

- `holdspeak/desktop_presence_cocoa.py` (PyObjC, lazy-imported behind the flag):
  - `_CocoaPresenceUI` — a **non-activating** `NSPanel`
    (`NSWindowStyleMaskNonactivatingPanel`, `NSStatusWindowLevel`, `hasShadow`,
    clear background, `ignoresMouseEvents`) hosting a **`WKWebView`** loaded at
    the local `/presence` URL (transparent webview so the page's rounded card +
    shadow show); positioned top-right; plus an **`NSStatusItem`** menu-bar glyph
    drawn in the state accent (with a contrasting halo so it reads on any bar).
  - `CocoaPresenceRenderer` (a `PresenceRenderer`) — drives the UI in a **child
    process** (spawn) over a command queue so AppKit owns its own runloop and the
    runtime is untouched; **lazy-starts** the child on first `show` (so the
    runtime URL is resolved after the server has a port). Degrades to no-op if
    the GUI session/PyObjC is unavailable.
  - `cocoa_presence_available()` — AppKit+WebKit import probe.
- `holdspeak/desktop_presence.py` — `_select_presence_renderer(platform,
  url_provider)` picks `CocoaPresenceRenderer` on macOS when WebKit + a URL
  provider are present; `build_desktop_presence_host(url_provider=…)` threads it.
- `holdspeak/web_runtime.py` — passes `url_provider=lambda: self.runtime_url`
  (read lazily at first show).
- `pyproject.toml` — the `presence` optional-extra (`pyobjc-framework-Cocoa` +
  `-WebKit`, darwin-gated); the venv was moved to a uv-managed CPython 3.13.11 so
  these install cleanly (separate toolchain commit).
- `scripts/presence_macos_smoke.py` — live smoke + screenshot harness.

## Verification artifacts

- **Live native capture** (`uv run python scripts/presence_macos_smoke.py`):
  - `evidence/macos_presence_hud.png` — the real `NSPanel` + `WKWebView` HUD with
    **native rounded corners + drop shadow**, rendering the Signal card (blue
    "Transcribing" ring · "Turning your speech into text…" · `Hotkey`). Visually
    identical to the web HUD, now a native window.
  - `evidence/macos_presence_glyph.png` — the menu bar with the color-keyed
    `NSStatusItem` glyph present.
  - **Focus-safety proven:** `frontmost before: Terminal | after: Terminal |
    focus_stolen: False` — showing the non-activating panel did **not** change
    the frontmost app, so injected dictation keystrokes keep landing in the
    target app. `SMOKE PASSED`.
- Unit (no GUI): `tests/unit/test_desktop_presence.py` — macOS selection picks
  the Cocoa renderer when WebKit available, None without WebKit, None without a
  URL provider; the build-host fallback paths.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  `2251 passed, 16 skipped` (2248/16 after the toolchain fix; +3). No GUI dep in
  the default suite (flag off → renderer not selected).

## Acceptance criteria — re-checked

- [x] With the flag on (macOS), the menu-bar glyph + the floating HUD render and
      track state; **focus is never stolen** — proven by the smoke run.
- [x] PyObjC/WebKit absent ⇒ graceful fallback (Cocoa not selected → host None →
      web card); default suite unaffected.
- [x] Rich Signal (it *is* the web card, in a native shadowed/rounded panel);
      screenshots captured.

## Deviations from plan

- The menu-bar glyph renders + is color-keyed, but a 16px dot is hard to isolate
  cleanly against a wallpaper-tinted menu bar; the HUD is the headline proof. A
  crisper template-style glyph is a polish candidate (noted for closeout).
- Lazy child-process start (not at construction) so the renderer can be wired at
  `WebRuntime.__init__` before the server has a URL.
- The live native screenshot is GUI-session-dependent, so it's produced by the
  smoke **script**, not the pytest suite (the suite covers selection/fallback).
