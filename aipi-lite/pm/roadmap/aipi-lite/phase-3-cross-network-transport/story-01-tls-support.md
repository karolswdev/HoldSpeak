# AIPI-3-01 - TLS (wss://) Support + URL/Scheme Handling

- **Project:** aipi-lite
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** AIPI-3-02, AIPI-3-05
- **Owner:** unassigned

## Problem

The bridge today connects via plain `ws://<host>:<port>/api/devices/audio`.
For cross-network operation the user may put HoldSpeak behind a TLS-
terminating fronting (Cloudflare Tunnel, a reverse proxy on the
HoldSpeak host, or HS-15's planned TLS termination point). The bridge
needs to speak `wss://` and choose between system-trust-store
verification and an explicit "skip verify" mode for self-signed
setups.

## Scope

### In

- Accept `wss://` (TLS) as well as `ws://` (plain) in the bridge
  config. Two design options to choose between:
  1. **Single `HOLDSPEAK_URL` env var** — e.g.,
     `HOLDSPEAK_URL=wss://holdspeak.tail-1234.ts.net/api/devices/audio`.
     Replaces `HOLDSPEAK_HOST` + `HOLDSPEAK_PORT` + an implicit path.
  2. **Add `HOLDSPEAK_SCHEME=wss`** alongside the existing host/port
     env vars. Default `ws`.
  Decide in this story; lean toward option 1 since it's more
  flexible (paths, port-in-URL) and less code.
- Pass `ssl=...` through to `websockets.connect()` when the URL is
  `wss://`. Build an `ssl.SSLContext` that uses the system trust
  store by default.
- Optional `HOLDSPEAK_INSECURE_SKIP_VERIFY=true` knob for
  self-signed setups (Cloudflare-Tunnel-with-default-cert, dev
  tunnels, etc.). Loud structured-warn on startup when set so it's
  obvious the bridge is running insecurely.
- Update `--check` to validate the TLS handshake (a `wss://` URL
  with a bad cert + verify-on should fail at handshake with a
  clear error).
- Mirror inbound close-code handling: TLS handshake failures show up
  before the WS handshake — surface them with a distinct error
  message so the user sees "TLS verification failed" rather than a
  generic socket error.

### Out

- Tunnel/VPN setup itself (AIPI-3-02).
- Per-device PSK schema (AIPI-3-04).
- Latency tuning across the link (AIPI-3-03).
- Custom CA bundles (revisit if users need it).

## Acceptance Criteria

- [ ] `bridge.env.example` documents the URL/scheme schema choice.
  If we go with `HOLDSPEAK_URL`, it documents the format with
  `wss://` example. If we go with the scheme env var, it
  documents `HOLDSPEAK_SCHEME` + the existing host/port.
- [ ] `bridge.py --check` against a `wss://` HoldSpeak with a
  valid cert succeeds (exit 0).
- [ ] `bridge.py --check` against a `wss://` HoldSpeak with a
  self-signed / bad cert fails (exit 1) with an error mentioning
  "TLS" or "certificate" — i.e., the failure mode is legible.
- [ ] `HOLDSPEAK_INSECURE_SKIP_VERIFY=true` makes the bad-cert case
  succeed with a structured warning logged
  (`tls.insecure_skip_verify_active`).
- [ ] All existing `ws://` tests + smoke paths still work
  unchanged. `pytest tests/ -q` passes.
- [ ] Unit tests for the URL parsing / scheme handling (whichever
  shape we land on).

## Test Plan

- **Unit:** URL/scheme parsing — fixtures for `ws://`, `wss://`,
  with and without ports, with and without paths. `pytest`.
- **Integration (manual):**
  1. Stand up HoldSpeak behind a local reverse proxy (caddy with a
     self-signed cert, or `socat` for a quick TLS terminator) on
     port 8443.
  2. Run `bridge.py --check` with `HOLDSPEAK_URL=wss://localhost:8443/api/devices/audio`.
     Expect a TLS-cert error.
  3. Set `HOLDSPEAK_INSECURE_SKIP_VERIFY=true` + retry. Expect
     exit 0 + a warning log.
  4. Use a real cert (mkcert; `caddy` with a `tls internal` block;
     or Cloudflare Tunnel with a real public name) and confirm
     verify-on works.

## Notes

- The Python `websockets` library accepts a pre-built `ssl.SSLContext`
  via `connect(uri, ssl=ctx)`. Build it with
  `ssl.create_default_context()` and either keep the defaults or
  flip `check_hostname=False` + `verify_mode=ssl.CERT_NONE` for the
  insecure path.
- `pydantic-settings` handles URL types via `pydantic`'s `AnyUrl` /
  `WebsocketUrl`; using one of those in the `Settings` model gives
  free validation. Worth checking whether `WebsocketUrl` distinguishes
  ws/wss — last I knew it did.
- Don't forget to update `_check`, `_run`, `_send_test_audio`, and
  `_audio_loopback` — all four call sites build the URL today.
  Centralise the URL construction in a single helper to keep them in
  sync.
- Heartbeat/audio frame logic does not change; TLS is invisible above
  the WS layer once the connection is up.
