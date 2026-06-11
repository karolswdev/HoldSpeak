# Evidence — HS-56-05: The native HUD frame

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

**One pure policy, two renderers** (`holdspeak/desktop_presence.py`):
- `presence_panel_frame(card_visible)` — passive is the **exact Phase-41
  geometry** (408×132, click-through); a presented card is 408×460,
  `interactive: True`. Interactive means pointer events ONLY; the
  focus-safety window flags (`NSWindowStyleMaskNonactivatingPanel` on macOS,
  `set_accept_focus(False)` on GTK) are not the policy's to touch and are
  asserted untouched by test.
- `PANEL_CARD_PROBE_JS` — both renderers learn about cards from the page
  itself (`#qlippy-card.is-in`, the HS-56-02 shell's contract): the activity
  payload cannot know about cards (they ride other broadcasts), so the page
  that owns the card lifecycle is the one honest source. Mascot-off can
  never grow the frame — the class never appears.

**macOS** (`desktop_presence_cocoa.py`): the NSPanel polls the page every
~0.4 s, applies the frame policy keeping the TOP edge fixed (Cocoa origins
are bottom-left; the panel grows downward from its top-right anchor — the
native anchor stays top-right, the open decision resolved), manages
`setIgnoresMouseEvents_` (off only while a card shows), and orders the panel
front for a card even when the activity policy has it hidden; `hide()`
defers to a live card (a proposal outlives the activity linger; ignoring is
still safe — the panel drops the moment the card resolves). The webview
autoresizes with the panel.

**Linux** (`desktop_presence_gtk.py`): the same policy on the GTK overlay —
`win.resize` (GTK origins are top-left, so the same downward growth is
free), and the input shape flips between empty (click-through) and full
(card up) while `accept_focus(False)` stays put.

## 2. Two real production bugs, found by real metal

Going live on the `.43` box (on user direction — a real machine with a real
X server) immediately exposed two latent Phase-41 bugs the code-only posture
would have kept shipping:

1. **Unpinned `Gdk` import.** `gi` resolves the NEWEST typelib, so on a box
   that also ships GTK4 (like `.43`), `from gi.repository import Gdk` grabs
   4.0 and Gtk 3.0's own Gdk-3.0 requirement then explodes
   (`ImportError: Requiring namespace 'Gdk' version '3.0', but '4.0' is
   already loaded`). Latent on GTK3-only machines. Fixed:
   `gi.require_version("Gdk", "3.0")` before the import.
2. **fork-from-threads deadlocked the overlay child.** By first show the
   runtime is multi-threaded (uvicorn is up), and the `fork`-context GTK
   child hung before signaling ready — every time under a running server
   (`GTK presence overlay timed out starting; notification-only.`),
   instantly fine without one (0.2 s single-threaded). This is exactly the
   configuration production runs in. Fixed: `forkserver` (children come from
   a clean single-threaded server process; unlike `spawn` it never
   re-imports the caller's `__main__`).

## 3. Live proof on real Linux metal (192.168.1.43, GNOME on Xorg)

`dogfood_story05_linux.py` (runs on `.43`) + `dogfood_story05_linux_orchestrator.py`
(runs on the Mac; SSH tunnel for the geometry oracle, real `xdotool` for the
click). No mocks: the production `build_desktop_presence_host` wiring →
`FreedesktopPresenceRenderer` → the real GTK WebKit overlay of the real
`/presence` page; a real aftercare proposal's real broadcast slides the card
out inside it:

```
· X11 screen 1920x1080; overlay region at x=1490, y=38
PASS  card-frame screenshot captured on the real X server
· clicking Approve at screen (1702,370) with xdotool…
PASS  X11 active window unchanged across the click (44040215)
PASS  a REAL xdotool click on the overlay's Approve recorded the audited
      decision (status=approved, by='web-user') — no side effect
RESULT: PASS
```

The X server's own geometry log across a second full pass (xwininfo):

```
— pre-card:        408x132+1490+38
— card up:         408x460+1490+38
— after Approve:   408x132+1490+38
```

Same origin throughout — anchored, growing downward, returning to the exact
passive frame on resolution. Screenshots reviewed:
`story05-linux-card-frame.png` (the full alert card — sprite, bang glyph,
real preview, the three G privacy answers, Approve/Decline — floating over
the user's actual desktop) and `story05-linux-passive-frame.png`
(post-resolution).

The server-bind detail: the dogfood first tried `0.0.0.0` and the runtime
**correctly refused** (no auth token — the Phase-50 guard held); loopback +
SSH tunnel is the documented pattern.

## 4. macOS posture (honest)

The Mac's screen stayed locked through the run (`CGSSessionScreenIsLocked:
True`, frontmost `loginwindow`), and the user waived the live macOS click
("we can call the phase good"). Verified on this Mac regardless: the
renderer child boots and orders the panel up at the passive frame. The
interactive-card seam is the same shared policy + probe proven live on
Linux; the macOS-specific glue (top-edge-fixed resize, `ignoresMouseEvents`
toggle, hide-defers-to-card) is unit-tested. `dogfood_story05_macos.py`
ships ready to run in any unlocked session (geometry oracle → real Quartz
click → frontmost-app focus assertion).

## 5. Tests + suite

`tests/unit/test_presence_panel_frame.py` — 11 tests: the passive frame IS
the Phase-41 geometry (the mascot-off lock), the card frame sizes up
width-stable, fresh copies, the probe matches the shell contract, both
renderers source the policy + probe, pointer-events-only (the focus flags
asserted absent from the frame path), sync-only-on-change and
hide-defers-to-card on both renderers.

```
$ uv run pytest -q tests/unit/test_presence_panel_frame.py tests/unit/test_desktop_presence.py tests/unit/test_desktop_presence_freedesktop.py
40 passed in 0.06s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2601 passed, 17 skipped in 81.58s (0:01:21)
```

(2590 → 2601.) No web-bundle change in this story (Python only).
