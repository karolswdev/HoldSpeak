# Evidence — HS-72-08 — One live bus on the web

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **The inventory found FOUR private sockets, not two.** Beyond the known
  pair (`dashboard-app.js` on `/live`, `presence-app.js` on `/presence`),
  `setup-app.js` and `welcome-app.js` each opened their own `/ws` for
  first-dictation feedback. All four are gone.
- **`runtime-bus.js` is the sole `/ws` owner**, upgraded with the
  dashboard's hard-won robustness so every consumer inherits it: 15s
  keepalive ping, exponential backoff with jitter (500ms·2ⁿ capped at 12s),
  and a synthetic `bus_status` event
  (`{state: connecting|connected|reconnecting, reconnectAt}`) that the
  `/live` connection pill maps from. One `deliver()` pipeline serves wire
  frames AND `seedState()`, so DOM listeners (qlippy) see the seed too —
  previously the seed bypassed them. The bus exposes `window.__hsBus` for
  the `new Function`-evaluated Alpine factories, whose page loaders
  (`live.astro`, `setup.astro`, `welcome.astro`) now import the bus module
  first.
- **`dashboard-app.js`**: `connect()` subscribes (`"*"` → the untouched
  `handleMessage` router; `bus_status` → connectionState + the two toasts);
  `cleanup()` unsubscribes; the private socket, `wsUrl`, ping and backoff
  machinery deleted. `closedByUser` was only ever a beforeunload latch — no
  user-facing close semantic existed to preserve.
- **`presence-app.js`**: subscribes + `seedState()`; its private socket and
  its duplicate `hs-activity`/`hs-broadcast` dispatches deleted (the bus
  dispatches once per frame — previously `/presence` double-fired
  `hs-activity`).
- **The vocabulary is written down once**:
  `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` gains "The one live bus"
  (wire frames, `bus_status`, the DOM re-dispatch, the `window.__hsBus`
  seam, and the do-not-open-your-own-socket rule).

## Preserved by design

- The server's WS frames — untouched (a client-side unification).
- `/api/devices/audio` — a different socket with its own PSK handshake.
- QueueHud's job synthesis from existing frames (`runtime_queue` as a
  backend feed stays a recorded follow-up).

## Verification artifacts (tests/e2e/test_live_bus.py, new)

- **One socket per page**: `/live`, `/dictation`, `/presence`, `/setup`
  each open exactly ONE runtime WebSocket (counted via Playwright's
  `websocket` events against the real app), zero page errors. `/live` —
  the page that owned a second socket by design since HS-69-07 — now rides
  the shell's.
- **A real broadcast reaches the widgets**: `server.broadcast("runtime_activity", …)`
  renders on the `/presence` card AND the `hs-activity` DOM re-dispatch is
  pinned by a pre-armed listener (found + fixed while writing it: an
  `evaluate()` whose expression value was the armed promise awaits itself —
  deadlock; the arrow-body form is load-bearing).
- **Reconnect recovery**: the server is stopped and a fresh one started on
  the same port; the page opens a second socket by itself (the backoff) and
  the reconnected stream renders a new broadcast.
- All three: **3 passed in 21s**. Route pre-flight **2 passed**; web build
  18 pages. One pre-existing marker test pinned the old private-socket
  idiom (`test_presence_hud_driver_consumes_runtime_activity`) — updated to
  pin the NEW contract (subscription + seed via the bus, and
  `new WebSocket` explicitly absent from presence-app). Full suite at
  ship: **3066 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] `runtime-bus.js` is the sole `/ws` owner; the second (and third and
      fourth) sockets are gone.
- [x] Every shell widget still fires (the DOM re-dispatch pinned by test;
      the seed now reaches DOM listeners too).
- [x] The dashboard's connection UX preserved (states, countdown, both
      toasts) via `bus_status`.
- [x] Reconnect proven against a real server restart.
- [x] The event vocabulary documented once.

## Deviations from plan

- Scope grew honestly: the story assumed two private sockets; the sweep
  found four (`setup-app.js`, `welcome-app.js`) and converted them in the
  same story — leaving them would have failed the "sole owner" criterion.

## Follow-ups

- A real `runtime_queue` backend frame so QueueHud stops synthesizing
  (recorded at scaffold; unchanged).
