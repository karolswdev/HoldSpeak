# HS-72-08 — One live bus on the web

- **Status:** done
- **Priority:** MED (two sockets, two dispatch vocabularies, one set of widgets)
- **Depends on:** —
- **Evidence:** [evidence-story-08.md](./evidence-story-08.md)

## Goal

The web runs two parallel live-event systems: `dashboard-app.js` owns a `/ws`
socket for `/live`, and `runtime-bus.js` deliberately opens a **second** `/ws`
on every page to feed the shell widgets (QueueHud, Qlippy, Waveform,
GenerationTheater, egress badge), with `presence-app.js` re-dispatching its
own overlapping DOM events. The duplication was a documented risk-avoidance
choice; it is now the thing that makes live behavior hard to reason about.
After this story there is one socket owner (`runtime-bus.js`), one DOM-event
vocabulary, and every consumer subscribes.

## Scope

- **In:** `runtime-bus.js` becomes the sole `/ws` owner (connect, reconnect,
  frame → typed DOM events, one documented event vocabulary);
  `dashboard-app.js` drops its own socket and subscribes (its
  meeting-control POSTs are untouched); `presence-app.js` rides the same bus
  (the native HUD webview constraint honored — the bus must work on the
  chromeless `/presence` page with no AppLayout); dead/duplicated dispatch
  paths deleted; the event vocabulary written down once (a short section in
  the web architecture doc).
- **Out:** the server's WS frame shapes (no backend change; the bus is a
  client-side unification); adding a `runtime_queue` frame so QueueHud stops
  synthesizing (a real backend follow-up — recorded, not built here);
  `device_audio_ws` (a different socket with its own PSK handshake, out of
  scope by design).

## Tasks

- [ ] Inventory every WS consumer + every `hs-*` DOM event producer/consumer
      (grep sweep committed in the evidence).
- [ ] Move socket ownership into the bus; make `/live` a subscriber; delete
      the second-connection path.
- [ ] Walk every shell widget live (a seeded meeting + a dictation pass):
      QueueHud fills, Qlippy cards arrive, waveform reacts, egress badge
      flips, presence HUD updates.
- [ ] Reconnect behavior proven (kill the server mid-session, restart, the
      bus recovers on every page).

## Proof required

One WebSocket connection per page in devtools (screenshot); the widget walk
screenshots; the reconnect capture; zero page errors on `/live`, `/presence`,
`/dictation`; full suite + web build green.

## Done

Shipped — and the inventory found FOUR private sockets, not two
(`setup-app.js` + `welcome-app.js` also owned one each). `runtime-bus.js`
is the sole `/ws` owner with the dashboard's robustness folded in (15s
ping, exponential backoff + jitter, the synthetic `bus_status` event the
/live connection pill maps from); one `deliver()` pipeline serves frames
AND the seed (DOM listeners now see the seed — previously bypassed);
`window.__hsBus` feeds the eval'd Alpine factories, whose loaders import
the bus first. The dashboard subscribes ("*" → its untouched router),
presence subscribes + seeds (its duplicate DOM dispatches gone — /presence
used to double-fire `hs-activity`), setup/welcome subscribe. The
vocabulary is documented once (ARCHITECTURE_WEB_FRONTEND "The one live
bus"). Proofs (`tests/e2e/test_live_bus.py`, real app + Playwright):
exactly one socket on /live, /dictation, /presence, /setup with zero page
errors; a real server broadcast rendering on the presence card with the
`hs-activity` re-dispatch pinned; reconnect proven against a full server
restart with a live post-restart broadcast — 3 passed. Full suite 3066
passed, 37 skipped. See [evidence-story-08.md](./evidence-story-08.md).
