# HS-25-02 — Web-Runtime Auth Token + Non-Loopback Bind Guard

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-25-07, (Phase 15)
- **Owner:** unassigned

## Problem

The FastAPI web runtime has no authentication: every route is open and the only
thing protecting transcripts, action items, speaker data, and config-mutation
endpoints is that the server binds `127.0.0.1` by default
(`web_server.py:378`, port resolved at `:466`, bind at `:469`). Phase 15's
explicit plan is to expose this runtime over a tunnel — which removes the only
safeguard. An auth gate must land before cross-network reach, not after.

## Scope

### In

- Add an authentication gate to the FastAPI app covering data-read and mutation
  endpoints (allow `/health` and static assets through).
- Reuse the existing device-PSK pattern: a token stored in config, compared with
  `hmac.compare_digest` (mirror `device_audio.verify_psk`,
  `device_audio.py:519`). Auto-generate on first run and auto-apply for the
  bundled local clients (web/menubar/TUI) so loopback use stays frictionless.
- Add a bind guard: refuse to bind a non-loopback host (`0.0.0.0`/LAN/`wss`
  fronting) unless a token is configured; emit a clear warning describing the
  exposure when a non-loopback bind is requested.
- Document the token + bind behavior.

### Out

- TLS termination and tunnel setup (Phase 15).
- Per-client / per-device distinct tokens (Phase 15 / device work).
- CSRF tokens and rate limiting (note as follow-ups; not required for a
  token-gated localhost/tunnel runtime).

## Acceptance criteria

- [x] Requests to data/mutation endpoints without a valid token return `401`
      **when bound off-loopback**; `/health`, `/api/devices/audio`, and `/_built`
      static assets stay open — `_web_auth_gate` middleware in `web_server.py`,
      covered by `tests/integration/test_web_auth_gate.py`.
- [x] Token comparison uses `hmac.compare_digest`; no token value is logged —
      `web_auth.verify_web_token`.
- [x] Default localhost launch is unchanged (loopback is open by the chosen
      policy; token is auto-generated + persisted via `ensure_web_token` so it is
      ready when a non-loopback bind appears). No manual step.
- [x] Binding a non-loopback host without a token is refused with an actionable
      error (`nonloopback_bind_blocked` → `RuntimeError` in `start()`); binding
      off-loopback with a token emits an exposure warning (`log.warning`).
- [x] `holdspeak doctor` reports auth + bind posture — `_check_web_auth`
      ("Web runtime auth").

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (auth or token or bind)"` — add
  cases over the FastAPI app using `httpx`/TestClient: missing token → 401,
  valid token → 200, `/health` open, non-loopback bind without token refused.
- Integration: local web client boot still reaches `/api/state` with the
  auto-applied token.
- Manual / device: launch with a non-loopback host and confirm the guard +
  warning. (Recorded in HS-25-07.)

## Notes / open questions

- Decide token transport for the bundled client (header vs. query for the
  WebSocket `/ws` and the device-audio WS, which already has its own PSK).
- The device-audio WebSocket (`/api/devices/audio`) keeps its existing PSK
  handshake; this story does not change it.
- Confirm whether any route currently assumes anonymous access from the Astro
  frontend before gating reads.

## Decision recorded

Auth is **enforced only off-loopback** (user decision 2026-05-31). Loopback binds
stay fully open — zero local friction, matching the long-standing "localhost is
trusted" model. The token is required to bind *and* on every request only when
the host is non-loopback. Token accepted via `X-HoldSpeak-Token`,
`Authorization: Bearer`, or `?token=` (the last lets browser navigation work over
a tunnel). `host` is hardcoded `127.0.0.1` today, so the gate is **dormant at the
default and activates the moment Phase 15 introduces a non-loopback bind**.

## Out of scope / follow-ups

- **`/ws` WebSocket token check off-loopback** — Starlette HTTP middleware does
  not cover WebSocket upgrades; the broadcast WS (duration ticks, low
  sensitivity) is not yet token-gated. Address when Phase 15 makes off-loopback
  real.
- **Browser token injection** — a polished off-loopback browser session needs the
  served JS to thread `?token=` into API calls; pairs with HS-25-08. Not needed
  while host is loopback-only.

## Closeout

Shipped 2026-05-31. See [evidence-story-02.md](./evidence-story-02.md).
