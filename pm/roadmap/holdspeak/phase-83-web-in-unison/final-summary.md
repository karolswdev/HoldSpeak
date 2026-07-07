# Phase 83 — Web in Unison: final summary

**CLOSED 4/4, 2026-07-07 — opened and shipped the same day.** The web desk
carries every conversation surface the iPad earned in the 2026-07-06 pass,
riding the hub wire those features already tested.

## What the phase shipped

- **HS-83-01 — Ground this ask** on the web composer: meetings expand to
  digest / transcript / each bound artifact, the gauge prices REAL fetched
  lengths against the picked profile's window and refuses past it, and the
  run ships references only — the hub hydrates, unknown ids refuse by name,
  and the kept card carries the grounding rows.
- **HS-83-02 — Agent conversations:** the rail's personas open persistent
  threads (`PersonaChat`); one hub call per turn
  (`POST /api/recipes/{id}/chat` — standing context + the KB honesty block +
  grounding + the 12-turn window; persists nothing); harvest is an explicit
  `/keep`; threads are device-local.
- **HS-83-03 — The models front door:** `GET /api/models` shares the ask
  route's allow-list derivation (no capability-by-400); the rail lists every
  runnable model; one click opens a chat pinned via the manifest-bounded
  `model` override through the same thread surface.
- **HS-83-04 — Docs + the live walk:** README + WEB_DESK.md entry points
  (guards green), and the four-beat walk on the REAL hub → the .43 llama.cpp:
  authenticated arrival, in-browser control-vs-treatment ("Mesh" vs
  "BLUE LANTERN"), a grounded persona thread, a pinned model chat — all
  asserted, 4 screenshots.

## The find of the phase

The live walk exposed that the entire web desk 401'd against a token-guarded
hub — the frontend never captured or attached the token, and loopback-bound
dev rigs could never see it. Fixed in the same story: the layout captures
`?token=…` once, scrubs the address bar, and attaches `X-HoldSpeak-Token` to
every same-origin request. The walk's authenticated arrival is the fix's
standing proof.

## Numbers

Four PRs (#281 open, #282, #283, #284, + the closing PR), hub sweep 3212+,
vitest 57, docs guards 18, api-surface at 246 routes, 10 committed
screenshots, two proof rigs + one live walk script that stay in `scripts/`
as the phase's regression rigs.

## What stays open (deliberate)

- `use_zone_context` is not assembled into web chat turns (the zone contract
  is not on that wire yet) — noted in story-02.
- The mobile track's HSM-15-07 docs story should point at the WEB_DESK.md
  feature descriptions instead of re-deriving them (noted in that story).
