# Evidence — HS-56-02: The dock + the card shell

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

- **`web/src/scripts/qlippy.js`** (~230 lines, framework-free like its
  sibling): the dock state machine (the RFC map: listening/recording/
  meeting_live → listening; transcribing/processing/saving/typing →
  thinking; error → error; complete → one 2 s `approve` flourish → idle;
  idle → `sleeping` after 5 min) and the **card shell** —
  `window.qlippyCard.present({sprite, glyph, headline, detail, preview,
  privacy, actions, sticky, autoDismissMs})` with a strict one-at-a-time
  FIFO queue (a "+N" hint for queued cards), pause-on-hover that re-arms
  after the hover ends, slide-out on resolve/dismiss, and an `aria-live`
  announcer. **Gated twice at boot** (`presence.enabled AND
  presence.mascot` from the existing `GET /api/settings`); with the flag
  off nothing un-hides and no listener runs. The shell itself contains no
  POST — the only fetch in the file is the gate read (locked by test); the
  event stories attach actions.
- **`presence.astro`**: a static, hidden Qlippy skeleton (dock + card bay +
  headline/detail/preview/privacy/actions/dismiss/queue-hint/announcer) so
  scoped CSS applies to everything textContent-filled; the **action buttons
  are the one JS-created element** and their styles live in an explicit
  `is:global` block per the Phase-54 rule. Sprite grammar:
  `background-size: 720px 80px` + `steps(9)` + `image-rendering: pixelated`
  (the dock scales via `transform: scale(0.7)` so the 9-frame
  background-position math stays exact — a real bug caught during the
  build: scaling by width/height desynced the fixed `-720px` keyframe).
  Motion: 420 ms in / 280 ms out on `cubic-bezier(0.16,1,0.3,1)`, the
  one-time settle bob + accent glow on alert cards; reduced motion pauses
  sprite loops and turns the slide into a fade.
- **`presence-app.js`** (+4 lines): re-dispatches the activity stream as a
  DOM `hs-activity` event and every `/ws` broadcast as `hs-broadcast`, so
  the mascot (and stories 03/04) ride the existing socket — no second
  WebSocket.

## 2. Live dogfood (real server, real settings API)

`dogfood_story02.py`:

```
PASS  flag off: ring-only HUD, no Qlippy node visible
PASS  dock follows the state map (listening → thinking → approve flourish → idle)
PASS  FIFO: dismissing the alert reveals the queued learned card (+1 hint shown)
PASS  pause-on-hover held the card past its 900 ms fuse
PASS  auto-dismiss resumed after the hover ended
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots committed and reviewed: `story02-dock-idle.png`,
`story02-dock-listening.png`, `story02-card-alert.png` (the full RFC
anatomy: sprite bay, glow border, mono preview, the privacy strip, Approve/
Decline, the "+1" hint, dock-Qlippy in the corner), `story02-card-learned.png`.

## 3. Tests + suite

`tests/integration/test_presence_qlippy_shell.py` — 5 locks: the static
hidden skeleton + announcer, the sprite grammar + reduced-motion pauses, the
motion-spec markers + the is:global button rule, the double gate + the
no-POST-in-the-shell invariant (`fetch(` count == 1), and the presence-app
re-dispatch hook.

```
$ uv run pytest -q tests/integration/test_presence_qlippy_shell.py
5 passed in 0.02s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2578 passed, 17 skipped in 81.43s (0:01:21)
```

(2573 → 2578.) Build clean; 0 `_built/` tracked.

## 4. Honest note on "byte-identical off"

The page's served HTML now contains the inert, `hidden` Qlippy skeleton
regardless of the flag (static markup is what keeps the scoped-CSS story
sane). The off-state guarantee is behavioral and proven live: nothing
renders, nothing listens, the ring HUD is unchanged.

## 5. Hand-off to 03/04

Present a card with:
`window.qlippyCard.present({sprite, glyph, headline, detail, preview,
privacy, actions: [{label, kind, onClick, resolves}], sticky})` — sticky for
actionable cards (they never auto-expire); listen via
`document.addEventListener("hs-broadcast", e => e.detail /* {type, data} */)`.
