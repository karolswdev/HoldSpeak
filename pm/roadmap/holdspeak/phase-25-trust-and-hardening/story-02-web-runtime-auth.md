# HS-25-02 — Web-Runtime Auth Token + Non-Loopback Bind Guard

- **Project:** holdspeak
- **Phase:** 25
- **Status:** backlog
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

- [ ] Requests to data/mutation endpoints without a valid token return `401`
      when a token is configured; `/health` and static assets remain open.
- [ ] Token comparison uses `hmac.compare_digest`; no token value is logged.
- [ ] Default localhost launch still works end-to-end for the bundled web client
      (token auto-generated + auto-applied) with no manual step.
- [ ] Binding a non-loopback host without a token is refused with an actionable
      error; binding with a token emits an exposure warning.
- [ ] `holdspeak doctor` reports whether the runtime is authenticated and how it
      is bound.

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
