# Phase 3 — Cross-Network Transport

**Last updated:** 2026-05-08 (phase opened — scaffold only).

## Goal

Make the AIPI-Lite + bridge usable when the user is **not on the same
LAN as HoldSpeak** — coffee shop, conference, AirBnB, friend's house.
Phase 1 made the device portable on the WiFi side; phase 2 made the
bridge a HoldSpeak satellite; phase 3 connects those two ends across
the public internet without exposing HoldSpeak's web runtime to the
world.

The bridge already speaks the WS protocol against any host:port — the
substantive work is:

- **TLS** so we can talk to HoldSpeak over `wss://` instead of plain
  `ws://` once HoldSpeak's web runtime grows TLS termination.
- **Tunnel / VPN choice** for the bridge → HoldSpeak path. Recommend
  one, document the alternatives.
- **Remote-friendly tuning** — bridge defaults assume sub-millisecond
  loopback; cross-network adds RTT in the 20–100 ms range and the
  occasional 1-second jitter spike.
- **PSK lifecycle for cross-network operation** — what happens when
  the user rotates the HoldSpeak PSK and the bridge isn't on the home
  LAN to update `bridge.env`?

This is **bridge-side + runbook-side work**. The device firmware
doesn't change in this phase — the device talks to whatever bridge is
on its local WiFi; the bridge's job is reaching HoldSpeak.

## Why this shape

Pairs with HoldSpeak **HS-15** (named but not yet scaffolded as a
HoldSpeak phase folder; see
`~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` §8 for the canonical list of
HS-15 deliverables: TLS termination point, PSK rotation under
reconnect, per-device PSKs, tunnel-vs-direct addressing, per-device
labels persisting across networks). The AIPI-Lite phases that
implement protocol changes pair 1:1 with HoldSpeak phases — AIPI-2 ⟷
HS-14, AIPI-3 ⟷ HS-15. AIPI-3 cannot finish before HS-15 does (the
TLS termination point + per-device PSK schema lives on the HoldSpeak
side); it CAN start now since the bridge-side TLS support and
tuning don't depend on HS-15.

Two paths considered + rejected:

- **Skip TLS, "trust your tunnel."** Tailscale / WireGuard already
  encrypt; doubling up with TLS over the tunnel is belt-and-braces.
  But: a user could choose Cloudflare Tunnel or just a port forward
  with no encryption layer, in which case the WS audio + PSK fly
  cleartext over the public internet. TLS at the WS layer is the
  trustworthy floor.
- **Public deployment of HoldSpeak.** Out of scope. HoldSpeak is a
  local-first product; running it as a public-internet service would
  redesign the auth, multi-tenant, and data-locality story. AIPI-3
  assumes HoldSpeak stays local + the user reaches it via tunnel/VPN.

## Scope

### In

- **TLS support in the bridge** — accept `wss://` URLs in
  `HOLDSPEAK_HOST` config (or a separate `HOLDSPEAK_SCHEME` knob),
  pass through to `websockets.connect`. Optionally support
  cert-skip for self-signed setups (Cloudflare, dev tunnels).
- **URL parsing** — today config has separate `HOLDSPEAK_HOST` +
  `HOLDSPEAK_PORT`; phase 3 may grow a single `HOLDSPEAK_URL` or
  similar to handle paths + schemes cleanly. Decide in story 01.
- **Remote-friendly defaults** — the WS leg's `ping_interval=15` /
  `ping_timeout=30` are fine for LAN; for cross-network we may need
  longer timeouts and/or smarter retry. Audio queue depth (today
  500 chunks) may also need adjusting if RTT grows + HoldSpeak's
  side is briefly slower to drain.
- **Tunnel / VPN choice + setup** — recommend Tailscale (free for
  personal use, magic DNS, mesh; both bridge host + HoldSpeak host
  on the tailnet). Document Cloudflare Tunnel and self-hosted
  WireGuard as alternatives.
- **PSK lifecycle for cross-network** — the bridge holds the PSK in
  `bridge.env` on the bridge host. Rotation requires updating that
  file. Document the procedure; consider whether a fetch-on-startup
  mechanism is worth building (probably not until pain is felt).
  Pairs with HoldSpeak HS-15's PSK-rotation-under-reconnect work.
- **Per-device PSKs** — if HoldSpeak HS-15 ships per-device secrets
  (replacing the single shared PSK), update the bridge's handshake
  to use the device-scoped value. Otherwise: defer.
- **Cross-network runbook** — `docs/HOLDSPEAK_BRIDGE.md` grows a §9
  "Using the bridge across networks" section, or a dedicated
  `docs/CROSS_NETWORK.md` if the content is large enough.

### Out

- **Public deployment of HoldSpeak.** AIPI-3 assumes HoldSpeak stays
  local; the bridge reaches it via tunnel/VPN.
- **Multi-tenant HoldSpeak** — each user has their own HoldSpeak
  install; cross-tenant secrets/data are not modelled.
- **Bridge running on the device itself** (no laptop in the loop).
  AIPI-Lite is an ESP32-S3 — running HoldSpeak's WS client + a
  tunnel client on it is a different product. Out forever.
- **Fully-managed identity** (mTLS client certs, OAuth, etc.).
  Phase 3 stays at PSK-in-config; richer identity is post-AIPI-3.

## Exit criteria (evidence required)

- [ ] Bridge can hand-shake against `wss://<host>` (TLS) via the
  `websockets` library, with optional cert-skip for self-signed.
- [ ] Bridge connects through at least one chosen
  tunnel/VPN (Tailscale recommended) end-to-end: device on
  network A, bridge + HoldSpeak both reachable on the user's
  tailnet, voice typing works.
- [ ] Cross-network latency measured + documented (button release
  → text typed) — expectation is sub-3-second in steady-state on
  a residential broadband + Tailscale link. If it's wildly
  worse, AIPI-3 surfaces it.
- [ ] PSK-rotation procedure documented for cross-network case
  (rotate on home network, copy new value into the bridge host's
  `bridge.env`, restart bridge).
- [ ] If HoldSpeak HS-15 ships per-device PSKs, bridge handshake
  uses the device-scoped value; if HS-15 hasn't shipped that yet,
  story 04 is `paused` with the dependency noted.
- [ ] `docs/HOLDSPEAK_BRIDGE.md` (or a dedicated `docs/CROSS_NETWORK.md`)
  covers the cross-network setup walkthrough.
- [ ] All AIPI-3-01..05 stories show `Status: done` with paired
  `evidence-story-{n}.md` files.
- [ ] `final-summary.md` records what shipped + what surprised us +
  handoff notes for AIPI-4 (wake-word / on-device VAD, currently
  the only phase past phase 3).
- [ ] `pm/roadmap/aipi-lite/README.md` reflects phase 3 done +
  phase 4 not-started; `Current phase` pointer moves accordingly.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AIPI-3-01 | TLS (wss://) support + URL/scheme handling | backlog | [story-01-tls-support.md](./story-01-tls-support.md) | — |
| AIPI-3-02 | Tunnel/VPN choice + cross-network addressing | backlog | [story-02-tunnel-and-addressing.md](./story-02-tunnel-and-addressing.md) | — |
| AIPI-3-03 | Remote-friendly tuning (timeouts, queue depths, knobs) | backlog | [story-03-remote-tuning.md](./story-03-remote-tuning.md) | — |
| AIPI-3-04 | PSK lifecycle + per-device PSKs (paired with HS-15) | backlog | [story-04-psk-lifecycle.md](./story-04-psk-lifecycle.md) | — |
| AIPI-3-05 | DoD + cross-network runbook + phase exit | backlog | [story-05-dod.md](./story-05-dod.md) | — |

(Status values: `backlog`, `in-progress`, `paused`, `done`, `cancelled`.)

## Where we are

Phase scaffolded 2026-05-08. AIPI-1 + AIPI-2 are
implementation-complete on disk; both are awaiting hardware
verification before close-out. AIPI-3 doesn't strictly block on
those — TLS support + tunnel choice can be implemented in parallel,
and verifying cross-network operation is what closes the loop on
phase 1 + 2's deferred testing anyway (the cross-network test rig
*is* the most stress-y verification path for the rest of the
substrate).

HoldSpeak HS-15 isn't scaffolded as a HoldSpeak phase folder yet
(as of 2026-05-07 the latest HoldSpeak phases are 0..14). The AIPI-3
plan references HS-15's named deliverables from
`~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` §8 but doesn't assume any
specific HS-15 implementation. Stories 01 and 03 land bridge-side
work that doesn't depend on HS-15 shipping; story 04 (PSK lifecycle)
is paired and may be `paused` until HS-15 has progressed.

Pickup: **AIPI-3-01** (TLS support) is the lowest-friction entry
point. The `websockets` library handles TLS transparently — the bulk
of the story is config schema + cert-skip handling for development /
self-signed setups, plus a runbook line.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| HoldSpeak HS-15 doesn't ship a TLS termination point in time, leaving the bridge's TLS support without a server to talk to | medium | The bridge can ship TLS support against any `wss://` URL — including a tunnel that wraps the loopback `ws://` (Cloudflare Tunnel terminates TLS at the edge; the underlying `ws://` is fine). HS-15 isn't a hard dep for AIPI-3-01. | If we want AIPI-3 to close cleanly with TLS-on-HoldSpeak, we wait for HS-15. If we want AIPI-3 to close earlier, we close with "TLS via tunnel layer is the supported path" + an HS-15 followup note. |
| Tailscale (recommended path) requires both ends on the tailnet — for a coffee-shop laptop running the bridge, the laptop is presumably already on the user's tailnet, but the *device* talks to the laptop over local WiFi (no tailnet needed there). If we ever wanted device-on-tailnet that's a much harder problem. | low | Phase 3 explicitly does NOT put the device on the tailnet. The device + bridge speak local WiFi; bridge speaks WAN. Documented decision. | n/a — design constraint. |
| Cross-network latency measurement reveals the WS protocol is too chatty (heartbeat every 15s × N reconnects → noticeable battery drain on the laptop) | low | Profile in story 03. The WS protocol is light; it's unlikely to be a problem. | If profiling shows real cost, tune ping_interval / heartbeat / backoff schedule and document the trade-offs. |
| PSK rotation in cross-network is genuinely awkward — user on coffee-shop WiFi can't easily SSH home to update bridge.env | medium | Story 04 documents the workflow + considers a fetch-on-startup option (bridge fetches PSK from HoldSpeak on connect using a one-time bootstrap token). Probably out of phase 3 scope unless the pain is real. | If users hit this in testing, build the bootstrap-token flow as a phase-3 followup or AIPI-4 story. |
| Per-device PSKs require coordinated change between HoldSpeak's `Config.device.psk` schema and the bridge's `HOLDSPEAK_PSK` env var | medium | Wait for HS-15 to ship its schema; mirror it. Story 04 stays `paused` if HS-15 hasn't shipped. | If HoldSpeak ships a different shape than expected (e.g. JSON-keyed rather than env), update story 04 + the runbook. |

## Decisions made (this phase)

- 2026-05-08 — **Recommend Tailscale as the cross-network transport.**
  Free for personal use, magic DNS makes addressing trivial, mesh
  topology means there's no central point to break. WireGuard +
  Cloudflare Tunnel are documented alternatives but not the
  default-recommended path.
- 2026-05-08 — **Bridge TLS support sits at the WebSocket layer
  (`wss://`).** Even if Tailscale already encrypts the link, layering
  TLS at the application means a user choosing a non-encrypting
  tunnel still gets confidential PSK + audio.
- 2026-05-08 — **The device stays on local WiFi only.** AIPI-Lite is
  an ESP32-S3; bringing Tailscale onto the device is a different
  product. The cross-network problem is bridge ↔ HoldSpeak.
- 2026-05-08 — **PSK distribution stays manual in v1.** A
  fetch-on-startup bootstrap is a nice-to-have but adds a chunk of
  protocol surface; defer until users hit the rotation pain in
  practice.

## Decisions deferred

- **Single `HOLDSPEAK_URL` env var vs. host+port+scheme triplet.**
  Single URL is more flexible (paths, schemes, ports in one place);
  triplet is what we have today and matches HoldSpeak's web runtime
  layout. Decide in story 01 once we have concrete cross-network
  setups to test against.
- **Cert pinning** vs. system-trust-store-only. For self-signed
  setups (a user running their own Cloudflare Tunnel, dev tunnels)
  we need at least an opt-in `INSECURE_SKIP_VERIFY`. Pinning is
  more secure but adds config surface. Default to system trust +
  insecure-skip; revisit if users need tighter control.
- **mDNS vs. Tailscale magic DNS for addressing.** Both could be
  supported. Document the trade-off in the runbook; let the user
  pick based on their setup.
- **Bootstrap-token flow for PSK rotation.** Out of phase 3 unless
  rotation pain becomes acute.
